import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import httpx
from hindsight_client import Hindsight
import anthropic

from backend.config import settings


def mask_key(key: str) -> str:
    if not key or key.strip() == "":
        return "<NOT SET>"
    clean_key = key.strip()
    if len(clean_key) <= 8:
        return "****"
    return f"{clean_key[:4]}...{clean_key[-4:]}"


def check_hindsight_connectivity() -> bool:
    print(f"\n--- Checking Hindsight Connectivity ---")
    print(f"Target URL: {settings.hindsight_base_url}")
    try:
        response = httpx.get(f"{settings.hindsight_base_url}/health", timeout=5.0)
        if response.status_code == 200:
            print(f"[PASS] Hindsight server is reachable and healthy.")
            return True
        else:
            print(f"[FAIL] Hindsight health check returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Failed to connect to Hindsight server at {settings.hindsight_base_url}: {e}")
        return False


def check_hindsight_retain_recall() -> bool:
    print(f"\n--- Checking Hindsight Retain -> Recall ---")
    print(f"Bank ID: {settings.hindsight_bank_id}")
    try:
        client = Hindsight(base_url=settings.hindsight_base_url)
        test_content = "Case Diary setup verification test observation."
        print(f"Retaining test observation...")
        retain_resp = client.retain(
            bank_id=settings.hindsight_bank_id,
            content=test_content
        )
        print(f"Retain response received successfully.")

        print(f"Recalling test observation...")
        recall_resp = client.recall(
            bank_id=settings.hindsight_bank_id,
            query="setup verification test observation"
        )
        print(f"[PASS] Hindsight retain -> recall test succeeded.")
        return True
    except Exception as e:
        err_msg = str(e)
        if settings.hindsight_api_llm_api_key:
            err_msg = err_msg.replace(settings.hindsight_api_llm_api_key, mask_key(settings.hindsight_api_llm_api_key))
        print(f"[FAIL] Hindsight retain -> recall test failed: {err_msg}")
        return False


def check_claude_connectivity() -> bool:
    print(f"\n--- Checking Claude API Connectivity ---")
    print(f"Anthropic Model: {settings.anthropic_model}")
    print(f"Anthropic Key: {mask_key(settings.anthropic_api_key)}")

    if not settings.anthropic_api_key or settings.anthropic_api_key.strip() == "":
        print(f"[FAIL] ANTHROPIC_API_KEY is not configured in .env.")
        return False

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Ping"}]
        )
        if response.content:
            print(f"[PASS] Claude API connected successfully.")
            return True
        else:
            print(f"[FAIL] Claude API returned empty content.")
            return False
    except Exception as e:
        err_msg = str(e)
        if settings.anthropic_api_key:
            err_msg = err_msg.replace(settings.anthropic_api_key, mask_key(settings.anthropic_api_key))
        print(f"[FAIL] Claude API check failed: {err_msg}")
        return False


def main():
    print("==========================================")
    print("   CASE DIARY - SETUP VERIFICATION        ")
    print("==========================================")

    hindsight_conn = check_hindsight_connectivity()
    hindsight_rr = check_hindsight_retain_recall() if hindsight_conn else False
    claude_conn = check_claude_connectivity()

    print("\n==========================================")
    print("   SUMMARY RESULTS                        ")
    print("==========================================")
    print(f"Hindsight Connectivity : {'[PASS]' if hindsight_conn else '[FAIL]'}")
    print(f"Hindsight Retain/Recall: {'[PASS]' if hindsight_rr else '[FAIL]'}")
    print(f"Claude API Connectivity: {'[PASS]' if claude_conn else '[FAIL]'}")
    print("==========================================")

    if hindsight_conn and hindsight_rr and claude_conn:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
