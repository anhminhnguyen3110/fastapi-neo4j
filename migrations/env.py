from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.db.models import Base

# Prefer reading the runtime DATABASE_URL from the app settings so
# `alembic upgrade head` works both in Docker and when running locally.
from app.config import settings

# If the app uses an async DB driver (postgresql+asyncpg) convert it to a
# sync URL for Alembic which runs synchronously (remove the +asyncpg
# suffix). If running inside Docker compose the URL will already point
# at the service name (postgres) which is fine for containerized runs.
db_url = settings.DATABASE_URL
if db_url and "+asyncpg" in db_url:
    # Replace the asyncpg driver token with psycopg (psycopg v3) so Alembic
    # (which runs synchronously) can connect using the installed driver.
    db_url = db_url.replace("+asyncpg", "+psycopg")

# Ensure alembic config uses our computed URL
if db_url:
    context.config.set_main_option("sqlalchemy.url", db_url)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Run migrations in 'online' mode.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()