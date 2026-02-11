from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    fdr_timeout: int = 30
    fdr_max_retries: int = 3
    fdr_base_delay: float = 1.0
    log_level: str = "INFO"
    alert_webhook_url: str = ""
    pythonutf8: int = 1

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
