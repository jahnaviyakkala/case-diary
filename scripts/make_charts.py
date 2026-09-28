"""
Draws the README charts as plain SVG (no plotting library needed).

    python scripts/make_charts.py            # uses live Hindsight recall for the learning curve
    python scripts/make_charts.py --offline  # reuses docs/charts/learning.json

Palette validated for colour-blind separation: proceeded #0E8A6A, adjourned #C2410C.
Adjournments are also drawn hollow, so the encoding never relies on colour alone.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.diary import diary  # noqa: E402

OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

INK, INK2, MUTED, LINE, SURFACE = "#14171C", "#3D434C", "#6A717A", "#E1E4DF", "#FCFCFB"
GREEN, ORANGE, GREY = "#0E8A6A", "#C2410C", "#A7ADA9"
FONT = "font-family=\"'Segoe UI', -apple-system, Helvetica, Arial, sans-serif\""
MONO = "font-family=\"ui-monospace, 'SF Mono', Consolas, monospace\""


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<rect width="{w}" height="{h}" rx="12" fill="{SURFACE}" stroke="{LINE}"/>{body}</svg>')


def text(x, y, s, size=12, fill=INK2, anchor="start", weight=400, mono=False):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" {MONO if mono else FONT}>{s}</text>')


def title(t, sub):
    return text(28, 38, t, 16, INK, weight=650) + text(28, 58, sub, 12, MUTED)


# ---------------------------------------------------------------- 1. Reddy timeline

def reddy_timeline():
    hs = diary.case_hearings("reddy-vs-state")
    nxt = diary.cases["reddy-vs-state"]["next_date"]
    d0, d1 = date.fromisoformat(hs[0]["date"]), date.fromisoformat(nxt)
    W, H, L, R, Y = 960, 250, 50, 40, 150
    x = lambda d: L + (date.fromisoformat(d) - d0).days / (d1 - d0).days * (W - L - R)
    b = [title("Reddy vs. State of Telangana: 14 hearings over three and a half years",
               "Each mark is a hearing. Hollow marks were adjourned at the prosecution's request.")]
    b.append(f'<line x1="{L}" x2="{W - R}" y1="{Y}" y2="{Y}" stroke="{LINE}" stroke-width="2"/>')
    for yr in range(d0.year + 1, d1.year + 1):
        xx = x(f"{yr}-01-01")
        b.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{Y - 6}" y2="{Y + 6}" stroke="{MUTED}"/>')
        b.append(text(xx, Y + 42, yr, 11, MUTED, "middle", mono=True))
    transfer = next(h for h in hs if h["judge"] == "J-KVR")
    tx = (x(transfer["date"]) + x(hs[transfer["no"] - 2]["date"])) / 2
    b.append(f'<line x1="{tx:.1f}" x2="{tx:.1f}" y1="78" y2="{Y + 24}" stroke="{MUTED}" stroke-dasharray="3 4"/>')
    b.append(text(tx + 6, 88, "Bench transferred", 11, MUTED))
    for h in hs:
        xx, adj = x(h["date"]), (h.get("adjournment") or {}).get("by") == "opposing"
        lift = 22 if h["no"] % 2 else 0
        if adj:
            b.append(f'<circle cx="{xx:.1f}" cy="{Y}" r="7" fill="{SURFACE}" stroke="{ORANGE}" stroke-width="2.5"/>')
            b.append(text(xx, Y + 24, h["adjournment"]["ground"], 10, ORANGE, "middle"))
        else:
            b.append(f'<circle cx="{xx:.1f}" cy="{Y}" r="7" fill="{GREEN}" stroke="{SURFACE}" stroke-width="2"/>')
        b.append(text(xx, Y - 16 - lift, f"H{h['no']}", 11, INK, "middle", 600, mono=True))
    xn = x(nxt)
    b.append(f'<circle cx="{xn:.1f}" cy="{Y}" r="8" fill="none" stroke="{INK}" stroke-width="2" stroke-dasharray="3 2"/>')
    b.append(text(xn, Y + 26, "Tomorrow", 11, INK, "middle", 650))
    lx = W - 330
    b.append(f'<circle cx="{lx}" cy="{H - 26}" r="6" fill="{GREEN}"/>' + text(lx + 12, H - 22, "Proceeded", 12))
    b.append(f'<circle cx="{lx + 110}" cy="{H - 26}" r="6" fill="{SURFACE}" stroke="{ORANGE}" stroke-width="2.5"/>'
             + text(lx + 122, H - 22, "Adjourned by prosecution", 12))
    (OUT / "reddy-timeline.svg").write_text(svg(W, H, "".join(b)), encoding="utf-8")


# ---------------------------------------------------------------- 2. one counsel, one bench, five matters

def counsel_pattern():
    """APP Chary's hearings before Sri K. Venkateswara Rao, one row per matter: the cross-case pattern."""
    hs = [h for h in diary.hearings.values() if h["counsel"] == "C-BNC" and h["judge"] == "J-KVR"]
    by_case = {}
    for h in hs:
        by_case.setdefault(h["case_id"], []).append(h)
    order = sorted(by_case, key=lambda c: max(h["date"] for h in by_case[c]), reverse=True)
    order.sort(key=lambda c: c != "reddy-vs-state")
    d0 = min(date.fromisoformat(h["date"]) for h in hs)
    d1 = date.fromisoformat(diary.today.isoformat())
    W, top, row, L, R = 960, 96, 40, 250, 40
    H = top + len(order) * row + 60
    x = lambda d: L + (date.fromisoformat(d) - d0).days / (d1 - d0).days * (W - L - R)
    b = [title("One prosecutor, one bench, five matters",
               "APP B. Narasimha Chary before Sri K. Venkateswara Rao. Hollow marks: he sought an adjournment.")]
    for yr in range(d0.year + 1, d1.year + 1):
        xx = x(f"{yr}-01-01")
        b.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{top - 14}" y2="{H - 50}" stroke="{LINE}"/>')
        b.append(text(xx, H - 32, yr, 11, MUTED, "middle", mono=True))
    for i, cid in enumerate(order):
        y = top + i * row + 10
        case = diary.cases[cid]
        adj = [h for h in by_case[cid] if (h.get("adjournment") or {}).get("by") == "opposing"]
        hero = cid == "reddy-vs-state"
        b.append(text(L - 16, y + 4, case["title"].replace(" of Telangana", ""), 12.5, INK if hero else INK2, "end", 650 if hero else 400))
        b.append(f'<line x1="{L}" x2="{W - R}" y1="{y}" y2="{y}" stroke="{LINE}" stroke-dasharray="2 4"/>')
        for h in sorted(by_case[cid], key=lambda h: h["date"]):
            xx = x(h["date"])
            if h in adj:
                b.append(f'<circle cx="{xx:.1f}" cy="{y}" r="6.5" fill="{SURFACE}" stroke="{ORANGE}" stroke-width="2.5"/>')
            else:
                b.append(f'<circle cx="{xx:.1f}" cy="{y}" r="5" fill="{GREY}"/>')
        b.append(text(W - R, y - 12, f"{len(adj)} of {len(by_case[cid])} adjourned" if adj else "no adjournments", 11,
                      ORANGE if adj else MUTED, "end", mono=True))
    lx = L
    b.append(f'<circle cx="{lx}" cy="{H - 14}" r="5" fill="{GREY}"/>' + text(lx + 12, H - 10, "Proceeded", 12))
    b.append(f'<circle cx="{lx + 100}" cy="{H - 14}" r="6" fill="{SURFACE}" stroke="{ORANGE}" stroke-width="2.5"/>'
             + text(lx + 112, H - 10, "Adjournment sought by APP Chary", 12))
    (OUT / "counsel-pattern.svg").write_text(svg(W, H, "".join(b)), encoding="utf-8")


# ---------------------------------------------------------------- 3. learning curve

MILESTONES = {3: ("Bank statement directed", 18, "middle"), 7: ("Amount changes in evidence", 18, "middle"),
              9: ("Passport promise", -12, "middle"), 12: ("Judge rejects 44-page note", 18, "middle"),
              13: ("Costs imposed on APP", -14, "end")}


def learning_curve(offline):
    cache = OUT / "learning.json"
    if offline and cache.exists():
        counts = json.loads(cache.read_text())
    else:
        from app import agent
        case = diary.case_view("reddy-vs-state")
        judge, counsel = case["judge_name"], case["opp_counsel_name"]
        facts, source = agent._recall_many([
            {"lane": "case", "query": "History of Reddy vs. State of Telangana: hearings, amounts, witnesses, objections",
             "tags": ["case:reddy-vs-state"], "budget": "high", "max_tokens": 8000},
            {"lane": "case", "query": "Directions, pending documents and promises to the client in Reddy vs. State",
             "tags": ["case:reddy-vs-state"], "budget": "high"},
            {"lane": "counsel", "query": f"Adjournments sought by {counsel} before {judge}",
             "tags": ["counsel:C-BNC"], "budget": "high"},
            {"lane": "judge", "query": f"How {judge} runs the court", "tags": ["judge:J-KVR"], "budget": "high"},
        ])
        if source != "hindsight":
            sys.exit("Hindsight unreachable; run with --offline to reuse the saved counts.")
        hs = diary.case_hearings("reddy-vs-state")
        counts = []
        for h in hs:
            own = sum(1 for f in facts if f["source"] and f["source"]["case_id"] == "reddy-vs-state" and f["source"]["no"] <= h["no"])
            other = sum(1 for f in facts if (not f["source"] or f["source"]["case_id"] != "reddy-vs-state")
                        and (f.get("date") or "9999") <= h["date"])
            counts.append({"no": h["no"], "own": own, "other": other})
        cache.write_text(json.dumps(counts, indent=1))

    W, H, L, R, T, B = 960, 330, 64, 40, 84, 64
    top = max(c["own"] + c["other"] for c in counts)
    ymax = (top // 20 + 1) * 20
    x = lambda n: L + (n - 1) / (len(counts) - 1) * (W - L - R)
    y = lambda v: H - B - v / ymax * (H - T - B)
    b = [title("The brief gets sharper as memory accumulates",
               "Facts Hindsight can recall for tomorrow's brief, if you had asked after each hearing.")]
    for v in range(0, ymax + 1, 20):
        b.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{LINE}"/>')
        b.append(text(L - 10, y(v) + 4, v, 11, MUTED, "end", mono=True))
    total = [(x(c["no"]), y(c["own"] + c["other"])) for c in counts]
    own = [(x(c["no"]), y(c["own"])) for c in counts]
    area = lambda pts, base: "M" + " L".join(f"{a:.1f},{b_:.1f}" for a, b_ in pts) + \
        f" L{pts[-1][0]:.1f},{base:.1f} L{pts[0][0]:.1f},{base:.1f} Z"
    b.append(f'<path d="{area(total, y(0))}" fill="{ORANGE}" fill-opacity="0.12"/>')
    b.append(f'<path d="{area(own, y(0))}" fill="{GREEN}" fill-opacity="0.18"/>')
    b.append(f'<polyline points="{" ".join(f"{a:.1f},{c:.1f}" for a, c in total)}" fill="none" stroke="{ORANGE}" stroke-width="2"/>')
    b.append(f'<polyline points="{" ".join(f"{a:.1f},{c:.1f}" for a, c in own)}" fill="none" stroke="{GREEN}" stroke-width="2"/>')
    for c in counts:
        xx = x(c["no"])
        b.append(text(xx, H - B + 20, f"H{c['no']}", 11, MUTED, "middle", mono=True))
        if c["no"] in MILESTONES:
            yy = y(c["own"])
            b.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4.5" fill="{GREEN}" stroke="{SURFACE}" stroke-width="2"/>')
    for n, (label, dy, anchor) in MILESTONES.items():
        c = counts[n - 1]
        b.append(text(x(n), y(c["own"]) + dy, label, 10.5, INK2, anchor))
    last = counts[-1]
    b.append(text(W - R, y(last["own"] + last["other"]) - 10, f"{last['own'] + last['other']} facts in all", 11.5, INK, "end", 650))
    ly = H - 22
    b.append(f'<rect x="{L}" y="{ly - 9}" width="12" height="12" rx="3" fill="{GREEN}"/>' + text(L + 18, ly + 1, "From this case", 12))
    b.append(f'<rect x="{L + 140}" y="{ly - 9}" width="12" height="12" rx="3" fill="{ORANGE}" fill-opacity="0.7"/>'
             + text(L + 158, ly + 1, "Plus the same bench and counsel in other matters", 12))
    (OUT / "learning-curve.svg").write_text(svg(W, H, "".join(b)), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    reddy_timeline()
    counsel_pattern()
    learning_curve(a.offline)
    print("charts written to", OUT)
