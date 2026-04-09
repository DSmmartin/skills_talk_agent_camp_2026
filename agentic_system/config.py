from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenAI provider ──────────────────────────────────────────────────────
    # Set to "azure" to use Azure OpenAI, leave as "openai" for default OpenAI.
    openai_provider: str = "openai"
    openai_model: str = "gpt-4o"

    # Default OpenAI (used when openai_provider = "openai")
    openai_api_key: str = ""

    # Azure OpenAI (used when openai_provider = "azure")
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment: str = "gpt-4o"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # ── ClickHouse ───────────────────────────────────────────────────────────
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "default"

    # ── MLflow ───────────────────────────────────────────────────────────────
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "ghost-contributors-demo"

    # ── Demo mode ────────────────────────────────────────────────────────────
    # Set to True when using `make seed LOCAL=1` (18-row controlled dataset).
    # Switches the default demo question and TUI hints to the local repo names.
    local_seed: bool = False

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = "WARNING"


settings = Settings()
