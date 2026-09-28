"""
The case diary: the advocate's own record of cases and hearings.

This is the system of record (what the advocate wrote down). The agent does not
read it directly when preparing briefs; it reads Hindsight memory. The diary is
used to render hearings into memory, to show the timeline, and as an offline
fallback when Hindsight is unreachable.
"""

import json
import re
import threading
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

from app.config import DATA_FILE, RUNTIME_DIR

_lock = threading.Lock()
_STOP = {"prep", "prepare", "for", "the", "tomorrow", "tomorrows", "hearing", "case", "matter", "brief", "and", "state",
         "vs", "versus", "telangana", "me", "today", "next", "what", "about", "others", "another"}
ANCHOR_FILE = RUNTIME_DIR / "anchor.json"
LOGGED_FILE = RUNTIME_DIR / "logged.json"


def _shift_days(anchor: date) -> int:
    """Shift every date so the dataset's anchor becomes tomorrow.

    The shift is fixed the first time it is computed, so memories retained into
    Hindsight keep matching the diary on later runs. Delete data/runtime/ (or run
    the seeder with --fresh) to re-anchor on a new day.
    """
    if ANCHOR_FILE.exists():
        return json.loads(ANCHOR_FILE.read_text())["shift_days"]
    shift = (date.today() + timedelta(days=1) - anchor).days
    ANCHOR_FILE.write_text(json.dumps({"shift_days": shift, "anchored_on": date.today().isoformat()}))
    return shift


def _shift(value, days):
    if not value:
        return value
    return (date.fromisoformat(value) + timedelta(days=days)).isoformat()


class Diary:
    def __init__(self):
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        anchor = date.fromisoformat(raw["anchor"])
        self.shift = _shift_days(anchor)
        self.today = anchor + timedelta(days=self.shift - 1)
        self.advocate = raw["advocate"]
        self.courts = raw["courts"]
        self.judges = raw["judges"]
        self.counsel = raw["counsel"]
        self.cases = {c["id"]: c for c in raw["cases"]}
        for c in self.cases.values():
            c["filed"] = _shift(c["filed"], self.shift)
            c["next_date"] = _shift(c.get("next_date"), self.shift)
        self.hearings = {}
        for h in raw["hearings"]:
            h["date"] = _shift(h["date"], self.shift)
            self.hearings[h["id"]] = h
        for h in self._load_logged():
            self._apply_logged(h)

    # -- persistence of hearings logged through the app ---------------------

    def _load_logged(self):
        if not LOGGED_FILE.exists():
            return []
        try:
            return json.loads(LOGGED_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _apply_logged(self, h):
        self.hearings[h["id"]] = h
        case = self.cases.get(h["case_id"])
        if case:
            case["next_date"] = h.get("next_date") or case.get("next_date")
            case["next_purpose"] = h.get("next_purpose") or case.get("next_purpose")

    def add_hearing(self, case_id, entry):
        with _lock:
            existing = self.case_hearings(case_id)
            no = (existing[-1]["no"] + 1) if existing else 1
            h = {
                "id": f"{case_id.upper()[:12]}-L{no:02d}", "case_id": case_id, "no": no,
                "date": entry.get("date") or self.today.isoformat(),
                "judge": self.cases[case_id]["judge"], "counsel": self.cases[case_id]["opp_counsel"],
                "stage": entry.get("stage") or self.cases[case_id].get("next_purpose") or "Hearing",
                "notes": entry["notes"].strip(), "asked": entry.get("asked", []),
                "adjournment": entry.get("adjournment"), "opp_args": [], "our_args": [], "due": entry.get("due", []),
                "promises": entry.get("promises", []), "outcome": entry.get("outcome", ""),
                "lesson": entry.get("lesson", ""), "next_date": entry.get("next_date"),
                "next_purpose": entry.get("next_purpose"), "logged": True,
            }
            logged = self._load_logged()
            logged.append(h)
            LOGGED_FILE.write_text(json.dumps(logged, indent=1, ensure_ascii=False), encoding="utf-8")
            self._apply_logged(h)
            return h

    # -- lookups -------------------------------------------------------------

    def case_hearings(self, case_id):
        return sorted((h for h in self.hearings.values() if h["case_id"] == case_id), key=lambda h: (h["date"], h["no"]))

    def find_case(self, text):
        """Resolve free text like 'reddy' or 'C.C. 1187' to a case, with suggestions when unsure."""
        q = text.lower().strip()
        if q in self.cases:
            return self.cases[q], []
        words = [w for w in re.findall(r"[a-z0-9]{3,}", q) if w not in _STOP]
        scored = []
        for c in self.cases.values():
            title = c["title"].lower()
            other = f"{c['case_no']} {c['client']['name']} {c['cnr']}".lower()
            score = SequenceMatcher(None, q, title).ratio() * 0.6
            for w in words:
                if w == c["short"].lower() or title.startswith(w):
                    score = max(score, 1.0)
                elif re.search(rf"\b{w}\b", title):
                    score = max(score, 0.85)
                elif w in other:
                    score = max(score, 0.75)
            scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        best = scored[0]
        suggestions = [c for s, c in scored[:4] if s > 0.45]
        if best[0] >= 0.75 and (len(scored) < 2 or best[0] > scored[1][0]):
            return best[1], []
        return None, suggestions

    def cause_list(self, days=7):
        horizon = (self.today + timedelta(days=days)).isoformat()
        start = self.today.isoformat()
        items = [c for c in self.cases.values() if c.get("next_date") and start <= c["next_date"] <= horizon]
        return sorted(items, key=lambda c: (c["next_date"], c["id"] != "reddy-vs-state", c["title"]))

    def case_view(self, case_id):
        c = self.cases[case_id]
        return {
            **c,
            "court_name": self.courts[c["court"]],
            "judge_name": self.judges[c["judge"]]["name"],
            "judge_designation": self.judges[c["judge"]]["designation"],
            "opp_counsel_name": self.counsel[c["opp_counsel"]]["name"],
            "opp_counsel_role": self.counsel[c["opp_counsel"]]["role"],
            "hearing_count": len(self.case_hearings(case_id)),
        }

    # -- rendering hearings for memory ---------------------------------------

    def render(self, h):
        """Turn a hearing record into the plain-language note that is retained in Hindsight."""
        c = self.cases[h["case_id"]]
        judge = self.judges.get(h["judge"], {"name": h["judge"], "designation": ""})
        counsel = self.counsel.get(h["counsel"], {"name": "opposite counsel", "role": ""})
        when = datetime.fromisoformat(h["date"]).strftime("%d %B %Y")
        lines = [
            f"Hearing {h['no']} in {c['title']} ({c['case_no']}) on {when}, before {judge['name']}, "
            f"{judge['designation']}, {self.courts[c['court']]}.",
            f"We (Adv. Ananya Rao) act for {c['client']['name']} ({c['client']['role']}). "
            f"Opposite counsel: {counsel['name']}, {counsel['role']}.",
            f"Stage: {h['stage']}.",
            h["notes"],
        ]
        adj = h.get("adjournment")
        if adj:
            who = {"opposing": f"sought by opposite counsel {counsel['name']}", "ours": "sought by us",
                   "court": "by the court on its own"}.get(adj["by"], adj["by"])
            lines.append(f"Adjournment {who}. Ground: {adj['ground']}. Reason given: {adj['reason']}.")
        for a in h.get("asked", []):
            lines.append(f"The judge asked / directed: {a}")
        for a in h.get("opp_args", []):
            lines.append(f"Opposite side argued: {a}")
        for a in h.get("our_args", []):
            lines.append(f"We argued: {a}")
        for x in h.get("due", []):
            lines.append(f"Document due from {x['by']}: {x['item']} (status: {x['status']}).")
        for p in h.get("promises", []):
            lines.append(f"Promise to client: {p}")
        if h.get("outcome"):
            lines.append(f"Outcome: {h['outcome']}")
        if h.get("lesson"):
            lines.append(f"Lesson noted by Adv. Ananya Rao: {h['lesson']}")
        return "\n".join(lines)

    def tags(self, h):
        c = self.cases[h["case_id"]]
        return [f"case:{c['id']}", f"judge:{h['judge']}", f"counsel:{h['counsel']}", f"court:{c['court']}"]

    def metadata(self, h):
        adj = h.get("adjournment") or {}
        return {
            "case_id": h["case_id"], "hearing_id": h["id"], "hearing_no": str(h["no"]), "date": h["date"],
            "judge": h["judge"], "counsel": h["counsel"], "adjourned_by": adj.get("by", "none"),
            "adj_ground": adj.get("ground", "none"),
        }

    # -- offline recall (used only when Hindsight is unreachable) ------------

    def keyword_recall(self, query, case_id=None, judge=None, counsel=None, limit=12):
        words = set(re.findall(r"[a-z0-9]{3,}", query.lower()))
        results = []
        for h in self.hearings.values():
            if case_id and h["case_id"] != case_id:
                continue
            if judge and h["judge"] != judge:
                continue
            if counsel and h["counsel"] != counsel:
                continue
            # Split the note into sentence-sized facts, like Hindsight's extracted facts.
            for line in self.render(h).split("\n")[2:]:
                low = line.lower()
                score = sum(low.count(w) for w in words) + 0.002 * h["no"]
                if score > 0.01 or case_id:
                    results.append({"text": line, "date": h["date"], "hearing_id": h["id"], "score": score,
                                    "type": "diary", "case_id": h["case_id"]})
        results.sort(key=lambda r: -r["score"])
        return results[: limit * 2]


diary = Diary()
