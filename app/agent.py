"""
The Case Diary agent.

brief()        recall from Hindsight -> compute cross-case patterns -> LLM brief with citations
ask()          free-form question over the whole practice's memory
log_hearing()  structure a dictated note, detect contradictions with memory, retain it
profile()      what memory has learned about a judge or opposite counsel

Each step degrades instead of failing:
  Hindsight down  -> offline recall from the local diary (flagged in the response)
  LLM down        -> a template brief assembled directly from recalled facts
  retain fails    -> the note is saved locally and queued for Hindsight
"""

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

from app import llm, prompts
from app.config import RUNTIME_DIR
from app.diary import diary
from app.memory import MemoryUnavailable, memory

log = logging.getLogger("case-diary.agent")
QUEUE_FILE = RUNTIME_DIR / "retain_queue.json"
_pool = ThreadPoolExecutor(max_workers=8)


# --------------------------------------------------------------------------
# Recall
# --------------------------------------------------------------------------

def _label(hearing_id):
    h = diary.hearings.get(hearing_id)
    if not h:
        return None
    c = diary.cases[h["case_id"]]
    return {"hearing_id": hearing_id, "case_id": c["id"], "case": c["short"], "title": c["title"],
            "no": h["no"], "date": h["date"]}


def _recall_many(queries, as_of=None):
    """Run several recalls in parallel. Returns (facts, source) where source is 'hindsight' or 'offline'."""
    futures = [_pool.submit(memory.recall, q["query"], tags=q.get("tags"), types=q.get("types"),
                            budget=q.get("budget", "mid"), max_tokens=q.get("max_tokens", 3000)) for q in queries]
    facts, source = [], "hindsight"
    try:
        for f, q in zip(futures, queries):
            for rank, fact in enumerate(f.result()):
                fact["lane"], fact["rank"] = q["lane"], rank
                facts.append(fact)
    except MemoryUnavailable:
        source = "offline"
        facts = []
        for q in queries:
            for r in diary.keyword_recall(q["query"], case_id=q.get("case_id"), judge=q.get("judge"),
                                          counsel=q.get("counsel"), limit=q.get("limit", 10)):
                r["lane"], r["rank"] = q["lane"], len(facts)
                facts.append(r)

    seen, unique = set(), []
    for fact in facts:
        key = fact["text"].strip().lower()[:160]
        if key in seen:
            continue
        seen.add(key)
        fact["source"] = _label(fact.get("hearing_id")) if fact.get("hearing_id") else None
        if as_of is not None and fact["source"] and fact["source"]["case_id"] == as_of[0] and fact["source"]["no"] > as_of[1]:
            continue
        if as_of is not None and fact["source"] and fact["source"]["date"] > as_of[2]:
            continue
        unique.append(fact)
    unique.sort(key=lambda f: (f.get("date") or ""), reverse=True)
    for i, fact in enumerate(unique, start=1):
        fact["fid"] = f"F{i}"
    return unique, source


def _select(facts, per_lane=None):
    """Pick facts for the prompt within a token budget (Groq's free tier allows ~8k tokens a minute).
    Within each lane, keep Hindsight's own relevance ranking; then present them in hearing order."""
    per_lane = per_lane or {"case": 45, "counsel": 14, "judge": 12, "ask": 30, "learned": 10}
    chosen = []
    for lane, cap in per_lane.items():
        lane_facts = sorted((f for f in facts if f.get("lane") == lane), key=lambda f: f.get("rank", 0))
        chosen += lane_facts[:cap]
    chosen += [f for f in facts if f.get("lane") not in per_lane][:10]
    chosen.sort(key=lambda f: (f["source"]["case_id"], f["source"]["no"]) if f.get("source") else ("", 0))
    return chosen


def _facts_block(facts, limit=90):
    lines = []
    for f in _select(facts)[:limit]:
        src = f["source"]
        where = f"{src['title']}, hearing {src['no']}, {src['date']}" if src else (f.get("date") or "undated")
        text = f["text"] if len(f["text"]) <= 260 else f["text"][:257] + "..."
        lines.append(f"[{f['fid']}] ({where}; {f['type']}) {text}")
    return "\n".join(lines) or "(no facts recalled)"


# --------------------------------------------------------------------------
# Cross-case patterns, computed only from hearings that memory surfaced
# --------------------------------------------------------------------------

def _counsel_pattern(case, facts):
    judge, counsel = case["judge"], case["opp_counsel"]
    surfaced = {f["source"]["hearing_id"] for f in facts if f.get("source")}
    hearings = [diary.hearings[h] for h in surfaced if h in diary.hearings]
    relevant = [h for h in hearings if h["judge"] == judge and h["counsel"] == counsel]
    by_case = {}
    for h in relevant:
        by_case.setdefault(h["case_id"], []).append(h)
    others = []
    for cid, hs in by_case.items():
        if cid == case["id"]:
            continue
        hs.sort(key=lambda h: h["date"])
        adj = [h for h in hs if (h.get("adjournment") or {}).get("by") == "opposing"]
        others.append({"case_id": cid, "title": diary.cases[cid]["title"], "last": hs[-1]["date"],
                       "adjourned": bool(adj), "grounds": sorted({h["adjournment"]["ground"] for h in adj}),
                       "hearings": [h["id"] for h in adj]})
    others.sort(key=lambda x: x["last"], reverse=True)
    recent = others[:4]
    in_case = [h for h in by_case.get(case["id"], []) if (h.get("adjournment") or {}).get("by") == "opposing"]
    if not recent and not in_case:
        return None
    grounds = [g for o in recent for g in o["grounds"]] + [h["adjournment"]["ground"] for h in in_case]
    return {
        "counsel": diary.counsel[counsel]["name"],
        "counsel_role": diary.counsel[counsel]["role"],
        "judge": diary.judges[judge]["name"],
        "matters": recent,
        "adjourned_matters": sum(1 for o in recent if o["adjourned"]),
        "total_matters": len(recent),
        "in_this_case": [{"hearing_id": h["id"], "no": h["no"], "ground": h["adjournment"]["ground"]}
                         for h in sorted(in_case, key=lambda h: h["no"])],
        "top_ground": max(set(grounds), key=grounds.count) if grounds else None,
    }


# --------------------------------------------------------------------------
# Brief
# --------------------------------------------------------------------------

def _clean_cites(obj, valid):
    """Drop citations the model invented; drop claims left with no valid citation."""
    def fix(item):
        if isinstance(item, dict) and "cites" in item:
            item["cites"] = [c for c in item.get("cites") or [] if c in valid]
        return item

    for key in ("bench_expects", "watch_outs", "promises", "carry", "changed"):
        items = [fix(x) for x in obj.get(key) or [] if isinstance(x, dict)]
        obj[key] = [x for x in items if x.get("cites")] if valid else items
    for key in ("last_time", "preempt"):
        if isinstance(obj.get(key), dict):
            fix(obj[key])
    obj.setdefault("gaps", [])
    return obj


def _template_brief(case, facts, pattern):
    """Used when the LLM is unavailable: facts laid out under the same headings, no prose generation."""
    def pick(pred, n=4):
        strip = re.compile(r"^(Promise to client|The judge asked / directed|Lesson noted by [^:]+):\s*")
        return [{"text": strip.sub("", f["text"]), "cites": [f["fid"]]} for f in facts if pred(f["text"].lower())][:n]

    own = [f for f in facts if f.get("source") and f["source"]["case_id"] == case["id"]]
    last = own[0] if own else None
    brief = {
        "headline": f"{case['next_purpose'] or 'Hearing'} — assembled directly from memory (language model offline).",
        "standing": case["summary"],
        "last_time": {"text": last["text"], "cites": [last["fid"]]} if last else {"text": "No record recalled.", "cites": []},
        "bench_expects": pick(lambda t: "judge asked" in t or "directed" in t),
        "watch_outs": [],
        "preempt": None,
        "promises": pick(lambda t: "promise" in t),
        "carry": pick(lambda t: t.startswith("document due")),
        "changed": [],
        "gaps": ["The language model was unavailable, so this brief lists recalled facts without synthesis."],
    }
    if pattern and pattern["adjourned_matters"]:
        brief["watch_outs"].append({
            "title": "Adjournment pattern",
            "text": f"{pattern['counsel']} sought adjournments in {pattern['adjourned_matters']} of the last "
                    f"{pattern['total_matters']} matters before {pattern['judge']}.", "cites": []})
    return brief


_brief_cache = {}
CACHE_SECONDS = 1800


def brief(case_id, use_memory=True, as_of_no=None, force=False):
    """Cached per (case, memory, depth, hearing count): a demo can flip views freely without
    burning the LLM's per-minute token quota. Logging a hearing changes the key, so it never goes stale."""
    key = (case_id, use_memory, as_of_no, len(diary.case_hearings(case_id)))
    hit = _brief_cache.get(key)
    if hit and not force and time.time() - hit[0] < CACHE_SECONDS and hit[1]["composer"] == "llm":
        return hit[1]
    result = _brief(case_id, use_memory, as_of_no)
    _brief_cache[key] = (time.time(), result)
    return result


def _brief(case_id, use_memory, as_of_no):
    case = diary.case_view(case_id)
    header = {
        "title": case["title"], "case_no": case["case_no"], "court": case["court_name"], "judge": case["judge_name"],
        "next_date": case.get("next_date"), "next_purpose": case.get("next_purpose"),
        "client": case["client"], "opp_counsel": case["opp_counsel_name"],
    }
    if not use_memory:
        return _generic_brief(case, header)

    judge = diary.judges[case["judge"]]["name"]
    counsel = diary.counsel[case["opp_counsel"]]["name"]
    tag_case = [f"case:{case_id}"]
    queries = [
        {"lane": "case", "query": f"History of {case['title']}: what happened at each hearing, amounts, witnesses, objections",
         "tags": tag_case, "budget": "high", "max_tokens": 6000, "case_id": case_id, "limit": 16},
        {"lane": "case", "query": f"What did the judge ask for or direct at the most recent hearings in {case['title']}? Pending documents.",
         "tags": tag_case, "case_id": case_id},
        {"lane": "case", "query": f"Promises made to the client {case['client']['name']} and lessons noted in {case['title']}",
         "tags": tag_case, "case_id": case_id},
        {"lane": "counsel", "query": f"Adjournments sought by {counsel} before {judge} and the grounds given",
         "tags": [f"counsel:{case['opp_counsel']}"], "budget": "high", "max_tokens": 5000,
         "counsel": case["opp_counsel"], "limit": 20},
        {"lane": "judge", "query": f"How {judge} runs the court: written submissions, adjournments, originals, what irritates the judge",
         "tags": [f"judge:{case['judge']}"], "judge": case["judge"]},
        {"lane": "judge", "query": f"What worked and what did not before {judge}; lessons noted",
         "tags": [f"judge:{case['judge']}"], "judge": case["judge"]},
    ]
    as_of = None
    if as_of_no:
        h = next((x for x in diary.case_hearings(case_id) if x["no"] == as_of_no), None)
        if h:
            as_of = (case_id, as_of_no, h["date"])
    facts, source = _recall_many(queries, as_of)
    pattern = _counsel_pattern(case, facts)

    user = (
        f"Tomorrow's cause-list entry:\n{json.dumps(header, ensure_ascii=False)}\n\n"
        f"Our client: {case['client']['name']} ({case['client']['role']}). Opposite counsel: {counsel}. Bench: {judge}.\n\n"
        f"Pattern computed from memory (cite the listed hearings if you mention it):\n{json.dumps(pattern, ensure_ascii=False)}\n\n"
        f"Memory facts (newest first):\n{_facts_block(facts)}"
    )
    composer = "llm"
    try:
        result = llm.chat(prompts.BRIEF_SYSTEM, user, json_mode=True, max_tokens=2200)
        result = _clean_cites(result, {f["fid"] for f in facts})
    except llm.LLMUnavailable:
        composer = "template"
        result = _template_brief(case, facts, pattern)

    return {
        "mode": "memory", "header": header, "brief": result, "pattern": pattern,
        "facts": [_public_fact(f) for f in facts], "memory_source": source, "composer": composer,
        "model": llm.last_model_used if composer == "llm" else None, "as_of": as_of_no,
        "hearing_count": case["hearing_count"],
    }


def _generic_brief(case, header):
    user = f"Cause-list entry for tomorrow:\n{json.dumps(header, ensure_ascii=False)}\nCase type: {case['type']}."
    composer = "llm"
    try:
        result = llm.chat(prompts.GENERIC_SYSTEM, user, json_mode=True, max_tokens=1800)
        result = _clean_cites(result, set())
    except llm.LLMUnavailable:
        composer = "template"
        result = {
            "headline": f"{case.get('next_purpose') or 'Hearing'} in {case['title']}.",
            "standing": "No history available. Check the physical case file and the last order sheet.",
            "last_time": {"text": "Unknown without the case diary.", "cites": []},
            "bench_expects": [], "watch_outs": [], "preempt": None, "promises": [],
            "carry": [{"text": "Case file and last order copy", "cites": []}], "changed": [],
            "gaps": ["Everything specific to this case."],
        }
    return {"mode": "stateless", "header": header, "brief": result, "pattern": None, "facts": [],
            "memory_source": None, "composer": composer, "model": llm.last_model_used if composer == "llm" else None}


def _public_fact(f):
    return {"fid": f["fid"], "text": f["text"], "type": f["type"], "date": f.get("date"),
            "source": f.get("source"), "lane": f.get("lane")}


# --------------------------------------------------------------------------
# Ask
# --------------------------------------------------------------------------

def ask(question, case_id=None):
    question = (question or "").strip()[:500]
    if not question:
        return {"answer": "Ask me something about your cases, a judge or opposite counsel.", "facts": []}
    if not case_id:
        found, _ = diary.find_case(question)
        case_id = found["id"] if found else None
    queries = [{"lane": "ask", "query": question, "budget": "high", "max_tokens": 5000, "limit": 14}]
    if case_id:
        queries.append({"lane": "case", "query": question, "tags": [f"case:{case_id}"], "case_id": case_id})
    facts, source = _recall_many(queries)
    try:
        answer = llm.chat(prompts.ASK_SYSTEM, f"Question: {question}\n\nMemory facts:\n{_facts_block(facts, 40)}",
                          max_tokens=900)
        composer = "llm"
    except llm.LLMUnavailable:
        composer = "template"
        answer = ("The language model is unavailable, so here are the most relevant things I remember:\n" +
                  "\n".join(f"- {f['text']} [{f['fid']}]" for f in facts[:5])) if facts else \
                 "I could not reach the language model and found nothing relevant in memory."
    return {"answer": answer, "facts": [_public_fact(f) for f in facts[:40]], "memory_source": source,
            "composer": composer, "case_id": case_id}


# --------------------------------------------------------------------------
# Log a hearing: structure -> contradiction check -> save -> retain
# --------------------------------------------------------------------------

def _structure(note, case):
    try:
        s = llm.chat(prompts.STRUCTURE_SYSTEM,
                     f"Case: {case['title']}. Today's date: {diary.today.isoformat()}.\n\nNote:\n{note}",
                     json_mode=True, max_tokens=1200)
        return s if isinstance(s, dict) else {}
    except llm.LLMUnavailable:
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", note)
        return {"summary": note, "next_date": m.group(1) if m else None}


def _detect_changes(note, case_id):
    title = diary.cases[case_id]["title"]
    facts, source = _recall_many([
        {"lane": "case", "query": note[:400], "tags": [f"case:{case_id}"], "budget": "high", "case_id": case_id, "limit": 20},
        # Contradictions usually hide in figures and statuses, which a note-shaped query can miss.
        {"lane": "case", "query": f"Amounts in rupees, dates, witness status and document status recorded in {title}",
         "tags": [f"case:{case_id}"], "case_id": case_id, "limit": 12},
    ])
    if not facts:
        return [], facts
    try:
        out = llm.chat(prompts.CONFLICT_SYSTEM, f"NEW NOTE:\n{note}\n\nEARLIER MEMORY:\n{_facts_block(facts, 60)}",
                       json_mode=True, max_tokens=2500, reasoning="medium")
    except llm.LLMUnavailable:
        return [], facts
    by_id = {f["fid"]: f for f in facts}
    changes = []
    for c in (out.get("changes") or [])[:5]:
        f = by_id.get(c.get("before_cite"))
        for k in ("before", "now", "topic"):
            c[k] = re.sub(r"\s*\(?(?:as per |per )?F\d+\)?", "", str(c.get(k) or "")).strip()
        changes.append({**c, "before_source": f["source"] if f else None})
    return changes, facts


def _queue(item):
    q = json.loads(QUEUE_FILE.read_text(encoding="utf-8")) if QUEUE_FILE.exists() else []
    q.append(item)
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False), encoding="utf-8")


def flush_queue():
    """Retry retains that failed while Hindsight was down. Returns how many are still waiting."""
    if not QUEUE_FILE.exists():
        return 0
    q = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    remaining = []
    for item in q:
        try:
            memory.retain(**item)
        except MemoryUnavailable:
            remaining.append(item)
    QUEUE_FILE.write_text(json.dumps(remaining, ensure_ascii=False), encoding="utf-8")
    return len(remaining)


def queued():
    return len(json.loads(QUEUE_FILE.read_text(encoding="utf-8"))) if QUEUE_FILE.exists() else 0


def log_hearing(case_id, note, hearing_date=None):
    case = diary.cases[case_id]
    note = note.strip()
    changes, _ = _detect_changes(note, case_id)
    s = _structure(note, case)

    adj = s.get("adjournment")
    if adj and adj.get("by") not in ("opposing", "ours", "court"):
        adj = None
    h = diary.add_hearing(case_id, {
        "date": hearing_date or diary.today.isoformat(),
        "stage": s.get("stage"), "notes": s.get("summary") or note, "asked": s.get("asked") or [],
        "adjournment": adj, "due": [d for d in s.get("due") or [] if isinstance(d, dict) and d.get("item")],
        "promises": s.get("promises") or [], "outcome": s.get("outcome") or "", "lesson": s.get("lesson") or "",
        "next_date": s.get("next_date"), "next_purpose": s.get("next_purpose"),
    })

    items = [{"text": diary.render(h), "document_id": h["id"], "when": h["date"], "tags": diary.tags(h),
              "metadata": diary.metadata(h), "context": "court hearing note"}]
    # A correction is retained as its own dated memory so recall surfaces the new
    # understanding next to (and newer than) the old fact, instead of silently overwriting it.
    for i, c in enumerate(changes):
        src = c.get("before_source")
        was = f" (recorded at hearing {src['no']}, {src['date']})" if src else ""
        items.append({
            "text": (f"Correction in {case['title']} as of hearing {h['no']} on {h['date']}: {c.get('topic')} is now "
                     f"'{c.get('now')}'. This supersedes the earlier record '{c.get('before')}'{was}."),
            "document_id": f"{h['id']}-corr{i + 1}", "when": h["date"], "tags": diary.tags(h),
            "metadata": {**diary.metadata(h), "kind": "correction"}, "context": "correction to earlier record",
        })

    retained, pending = 0, 0
    for item in items:
        try:
            memory.retain(**item)
            retained += 1
        except MemoryUnavailable:
            _queue(item)
            pending += 1
    return {"hearing": h, "changes": changes, "retained": retained, "queued": pending,
            "structured": s, "memory_error": memory.last_error if pending else None}


# --------------------------------------------------------------------------
# Profiles of judges and opposite counsel
# --------------------------------------------------------------------------

def profile(kind, pid):
    person = (diary.judges if kind == "judge" else diary.counsel)[pid]
    tag = f"{kind}:{pid}"
    q = (f"How does {person['name']} run the court across our cases: adjournments, written submissions, originals, what worked"
         if kind == "judge" else
         f"How does {person['name']} behave across our cases: adjournment requests and grounds, arguments, tactics")
    scope = {"judge": pid} if kind == "judge" else {"counsel": pid}
    facts, source = _recall_many([
        {"lane": kind, "query": q, "tags": [tag], "budget": "high", "max_tokens": 5000, "limit": 20, **scope},
        # Observations are patterns Hindsight consolidated on its own across many hearings.
        {"lane": "learned", "query": q, "tags": [tag], "types": ["observation"], "limit": 0, **scope},
    ])
    hs = [h for h in diary.hearings.values() if h[kind if kind == "judge" else "counsel"] == pid]
    stats = {
        "hearings": len(hs), "cases": len({h["case_id"] for h in hs}),
        "adjournments_by_opposite": sum(1 for h in hs if (h.get("adjournment") or {}).get("by") == "opposing"),
    }
    try:
        out = llm.chat(prompts.PROFILE_SYSTEM, f"Person: {person['name']} ({person.get('designation') or person.get('role')})\n\n"
                                               f"Memory facts:\n{_facts_block(facts, 40)}", json_mode=True, max_tokens=1200)
        out = {"summary": out.get("summary", ""),
               "points": [p for p in out.get("points") or [] if isinstance(p, dict)]}
        composer = "llm"
    except llm.LLMUnavailable:
        composer = "template"
        out = {"summary": "Recalled facts (language model offline).",
               "points": [{"text": f["text"], "cites": [f["fid"]]} for f in facts[:6]]}
    return {"person": {**person, "id": pid, "kind": kind}, "profile": out, "stats": stats,
            "facts": [_public_fact(f) for f in facts[:40]], "memory_source": source, "composer": composer}


def health():
    ok = memory.healthy()
    pending = flush_queue() if ok and queued() else queued()
    return {
        "hindsight": {"ok": ok, "bank": memory.bank, "error": None if ok else memory.last_error,
                      "stats": memory.stats() if ok else None},
        "llm": {"configured": llm.configured(), "model": llm.LLM_MODEL, "fallback": llm.LLM_FALLBACK_MODEL,
                "last_error": llm.last_error},
        "queued_retains": pending,
        "today": diary.today.isoformat(),
    }
