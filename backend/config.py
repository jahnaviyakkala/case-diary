import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from root .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings(BaseModel):
    hindsight_base_url: str = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888")
    hindsight_bank_id: str = os.getenv("HINDSIGHT_BANK_ID", "case-diary-demo")
    hindsight_api_llm_provider: str = os.getenv("HINDSIGHT_API_LLM_PROVIDER", "gemini")
    hindsight_api_llm_api_key: str = os.getenv("HINDSIGHT_API_LLM_API_KEY", "")
    hindsight_api_llm_model: str = os.getenv("HINDSIGHT_API_LLM_MODEL", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


settings = Settings()
