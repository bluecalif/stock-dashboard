from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    fdr_timeout: int = 30
    fdr_max_retries: int = 3
    fdr_base_delay: float = 1.0
    log_level: str = "INFO"
    alert_webhook_url: str = ""
    cors_origins: str = ""  # comma-separated extra origins for CORS
    pythonutf8: int = 1

    # LLM (OpenAI)
    openai_api_key: str = ""
    llm_pro_model: str = "gpt-5"
    llm_lite_model: str = "gpt-5-mini"

    # Auth / JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # LangSmith (optional — set via .env, no code changes needed)
    langchain_tracing_v2: str = ""
    langchain_api_key: str = ""
    langchain_project: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
