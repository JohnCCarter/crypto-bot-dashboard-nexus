import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Interpret the config file for Python logging.
config = context.config
fileConfig(config.config_file_name)

database_url = os.getenv("DATABASE_URL", "sqlite:///./local.db")
config.set_main_option("sqlalchemy.url", database_url)

from backend.persistence import Base  # noqa: E402
from backend.persistence.models import BotStatus  # noqa: F401,E402

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=database_url, target_metadata=target_metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
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
