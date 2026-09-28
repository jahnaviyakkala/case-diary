"""
Load the case diary into Hindsight memory.

    python scripts/seed_memory.py                 # core set: flagship case + everything sharing its bench or counsel
    python scripts/seed_memory.py --scope all     # all 505 hearings (uses more LLM credits on the Hindsight side)
    python scripts/seed_memory.py --fresh         # delete the bank and re-anchor dates to today, then seed

Seeding is resumable: progress is written to data/runtime/seeded.json, so a
rate limit or network drop halfway through just means running it again.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

parser = argparse.ArgumentParser()
parser.add_argument("--scope", choices=["core", "all"], default="core")
parser.add_argument("--fresh", action="store_true", help="delete the memory bank and local runtime state first")
parser.add_argument("--batch", type=int, default=5)
args = parser.parse_args()

if args.fresh:
    runtime = ROOT / "data" / "runtime"
    if runtime.exists():
        shutil.rmtree(runtime)

from app.diary import diary  # noqa: E402  (imported after --fresh so dates re-anchor)
from app.memory import MemoryUnavailable, memory  # noqa: E402
from app.config import RUNTIME_DIR, HINDSIGHT_URL  # noqa: E402

PROGRESS = RUNTIME_DIR / "seeded.json"


def core_case_ids():
    hero = diary.cases["reddy-vs-state"]
    ids = {hero["id"]}
    for c in diary.cases.values():
        if c["judge"] == hero["judge"] or c["opp_counsel"] == hero["opp_counsel"] or c["type"] == "Bail":
            ids.add(c["id"])
    # a spread of other matters so questions about the wider practice have something to find
    for c in list(diary.cases.values())[::4]:
        ids.add(c["id"])
    return ids


def main():
    print(f"Hindsight: {HINDSIGHT_URL}  bank: {memory.bank}")
    if args.fresh:
        print("Deleting existing bank ...")
        memory.reset()
    try:
        memory.ensure_bank()
    except MemoryUnavailable as exc:
        sys.exit(f"Cannot reach Hindsight: {exc}\nCheck HINDSIGHT_URL / HINDSIGHT_API_KEY in .env (see README).")

    done = set(json.loads(PROGRESS.read_text())) if PROGRESS.exists() else set()
    ids = core_case_ids() if args.scope == "core" else set(diary.cases)
    todo = [h for h in sorted(diary.hearings.values(), key=lambda h: h["date"])
            if h["case_id"] in ids and h["id"] not in done]
    print(f"{len(done)} hearings already in memory, {len(todo)} to retain ({args.scope} scope).")

    for i in range(0, len(todo), args.batch):
        chunk = todo[i:i + args.batch]
        items = [{"content": diary.render(h), "document_id": h["id"], "timestamp": h["date"] + "T10:30:00+05:30",
                  "context": "court hearing note", "tags": diary.tags(h), "metadata": diary.metadata(h)} for h in chunk]
        for attempt in range(4):
            try:
                memory._down_until = 0
                memory.retain_batch(items)
                break
            except MemoryUnavailable as exc:
                wait = 10 * (attempt + 1)
                print(f"  batch failed ({exc}); retrying in {wait}s")
                time.sleep(wait)
        else:
            sys.exit("Giving up for now. Run the same command again to resume.")
        done.update(h["id"] for h in chunk)
        PROGRESS.write_text(json.dumps(sorted(done)))
        print(f"  retained {min(i + args.batch, len(todo))}/{len(todo)}")

    print("Done. Hindsight keeps consolidating observations in the background for a few minutes.")
    try:
        memory.client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
