from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Event Intelligence OS"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://event_os:event_os_dev@localhost:5432/event_os"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Auth
    auth_disabled: bool = True
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"

    # Execution mode
    execution_mode: str = "replay"  # replay | shadow | paper | micro_live | live

    model_config = {"env_prefix": "EOS_", "env_file": ".env"}


settings = Settings()
