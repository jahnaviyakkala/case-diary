import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if value else default


# Hindsight: either Hindsight Cloud (URL + API key) or a local Docker instance (URL only).
HINDSIGHT_URL = _env("HINDSIGHT_URL", "http://localhost:8888").rstrip("/")
HINDSIGHT_API_KEY = _env("HINDSIGHT_API_KEY") or None
HINDSIGHT_BANK = _env("HINDSIGHT_BANK", "case-diary")

# Agent LLM: Groq's OpenAI-compatible endpoint by default. Any OpenAI-compatible
# provider works by changing LLM_BASE_URL.
LLM_BASE_URL = _env("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = _env("LLM_API_KEY") or _env("GROQ_API_KEY")
LLM_MODEL = _env("LLM_MODEL", "openai/gpt-oss-120b")
LLM_FALLBACK_MODEL = _env("LLM_FALLBACK_MODEL", "openai/gpt-oss-20b")

DATA_FILE = ROOT / "data" / "diary.json"
RUNTIME_DIR = ROOT / "data" / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
