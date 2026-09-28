"""
Checks that everything the demo needs is reachable. Safe to run any time.

    python scripts/check_setup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import llm  # noqa: E402
from app.config import HINDSIGHT_API_KEY, HINDSIGHT_URL, LLM_API_KEY, LLM_MODEL, ROOT  # noqa: E402
from app.memory import MemoryUnavailable, memory  # noqa: E402

OK, BAD, WARN = "  [ ok ]", "  [fail]", "  [warn]"


def main():
    failures = 0
    print("\nCase Diary setup check\n")

    if not (ROOT / ".env").exists():
        print(f"{BAD} .env not found. Copy .env.example to .env and fill in the keys.")
        failures += 1

    print(f"Hindsight at {HINDSIGHT_URL} ({'cloud key set' if HINDSIGHT_API_KEY else 'no API key, expecting local Docker'})")
    if memory.healthy():
        print(f"{OK} Hindsight is reachable")
        stats = memory.stats()
        if stats is None and ("404" in (memory.last_error or "") or "NotFound" in (memory.last_error or "")):
            print(f"{WARN} bank '{memory.bank}' does not exist yet (normal before seeding). Run: python scripts/seed_memory.py")
        elif stats is None or sum(stats.values()) == 0:
            print(f"{WARN} bank '{memory.bank}' is empty. Run: python scripts/seed_memory.py")
        else:
            print(f"{OK} bank '{memory.bank}': {stats['world']} facts, {stats['experience']} experiences, "
                  f"{stats['observation']} learned observations")
            try:
                memory.recall("adjournment", budget="low", max_tokens=200)
                print(f"{OK} recall works")
            except MemoryUnavailable as exc:
                print(f"{BAD} recall failed: {exc}")
                failures += 1
    else:
        print(f"{BAD} Hindsight unreachable: {memory.last_error}")
        failures += 1

    print(f"\nLLM {LLM_MODEL}")
    if not LLM_API_KEY:
        print(f"{BAD} LLM_API_KEY is empty")
        failures += 1
    else:
        try:
            reply = llm.chat("Reply with the single word: ready", "ping", max_tokens=50)
            print(f"{OK} {llm.last_model_used} answered: {reply[:40]!r}")
        except llm.LLMUnavailable as exc:
            print(f"{BAD} {exc}")
            failures += 1

    print("\nAll good. Start the app: python -m uvicorn app.main:app --port 8000\n" if not failures else
          f"\n{failures} problem(s). The app still runs in degraded mode, but fix these for the full demo.\n")
    try:
        memory.client.close()
    except Exception:
        pass
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
