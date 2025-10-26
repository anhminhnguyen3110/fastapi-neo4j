from pydantic import AnyUrl
import os
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # App
    NODE_ENV: str = "development"
    PORT: int = 3000
    HOST: str = "0.0.0.0"

    # Neo4j
    NEO4J_URI: AnyUrl
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"

    # Postgres
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "embeddb"
    DATABASE_URL: Optional[str] = None

    # Embed / runtime
    EMBED_BASE_URL: Optional[AnyUrl] = None
    MAX_TOKEN_EXPIRY_DAYS: int = 90
    DEFAULT_TOKEN_EXPIRY_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# If DATABASE_URL not provided via env, build a sensible default using
# Postgres fields so the app can run locally against localhost:5432 when
# docker-compose or a local Postgres maps that port.
if not settings.DATABASE_URL:
    settings.DATABASE_URL = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DB}"
    )

# If the DATABASE_URL was set to use the docker-compose service host `postgres`
# but we're running the app locally (not inside the compose network), swap
# that hostname to `localhost` so the process can connect to a mapped port.
if settings.DATABASE_URL and "@postgres:" in settings.DATABASE_URL and not os.environ.get("IN_DOCKER"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("@postgres:", "@localhost:")
