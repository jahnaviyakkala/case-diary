from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hindsight_url: str = "http://localhost:8888"
    hindsight_base_url: str = "http://localhost:8888"
    hindsight_bank_id: str = "case-diary-demo"
    hindsight_api_llm_provider: str = "gemini"
    hindsight_api_llm_api_key: str = ""
    hindsight_api_llm_model: str = "gemini-2.0-flash"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    database_url: str = "sqlite:///data/case_diary.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
