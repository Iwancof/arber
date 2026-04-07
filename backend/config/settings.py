from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Event Intelligence OS"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://event_os:event_os_dev@localhost:50002/event_os"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    host: str = "0.0.0.0"
    port: int = 50000

    # Auth
    auth_disabled: bool = True
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"

    # Anthropic API (LLM Worker)
    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-opus-4-6"
    anthropic_model_event_extract: str = ""  # falls back to default
    anthropic_model_forecast: str = ""  # falls back to default
    anthropic_max_tokens: int = 4096
    anthropic_timeout_sec: int = 120

    # Alpaca API (Market Data + Broker + News)
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_data_url: str = "https://data.alpaca.markets"

    # Execution mode
    execution_mode: str = "replay"  # replay | shadow | paper | micro_live | live

    model_config = {"env_prefix": "EOS_", "env_file": ".env"}


settings = Settings()
