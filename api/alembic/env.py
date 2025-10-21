"""
Alembic environment configuration for SAFE-BMAD system
"""
import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add shared modules to Python path
sys.path.append("../shared")

from alembic import context
from shared.config.settings import get_settings

# Import all models to ensure they are registered with SQLAlchemy
# We'll import these after creating the models
# from models.base import Base
# from models.user import User
# from models.scenario import Scenario
# from models.agent import Agent
# from models.analysis import Analysis
# from models.decision import Decision
# from models.resource import Resource
# from models.message import Message
# from models.associations import UserScenario

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# target_metadata = Base.metadata
target_metadata = None

# Get database URL from settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
        render_item=render_item
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    configuration = config.get_section(config.config_ini_section)
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


def include_object(object, name, type_, reflected, compare_to):
    """
    Custom function to include/exclude objects from migrations.
    """
    # Exclude certain tables or objects if needed
    if type_ == "table" and name in ["alembic_version"]:
        return False
    return True


def render_item(type_, obj, autogen_context):
    """
    Custom rendering for migration items.
    """
    # Add custom rendering logic if needed
    if type_ == "index" and hasattr(obj, 'info') and 'skip' in obj.info:
        return False
    return False


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()