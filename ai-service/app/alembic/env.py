import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.settings import env_settings
from app.db_models.base_entity import Base

# Import all models so they're registered with SQLAlchemy's metadata

# Alembic config
config = context.config

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata
target_metadata = Base.metadata


# Database URL từ .env
def get_url():
    user = env_settings.POSTGRES_USER
    password = env_settings.POSTGRES_PASSWORD
    host = env_settings.POSTGRES_HOST
    port = env_settings.POSTGRES_PORT
    db = env_settings.POSTGRES_DB
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# Offline migrations
def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Async online migrations
async def run_migrations_online():
    url = get_url()
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
