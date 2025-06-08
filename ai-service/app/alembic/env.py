from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.settings import env_settings

# Import all models so they're registered with SQLAlchemy's metadata
from app.db_models import *  # noqa: F403, F401
from app.db_models.base_entity import Base

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
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


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


# Online migrations
def run_migrations_online():
    url = get_url()
    connectable = create_engine(url)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
