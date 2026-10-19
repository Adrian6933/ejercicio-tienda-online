from alembic import context
from app.config import Settings
from app.database import Base, make_engine
from app import models  # noqa: F401

config = context.config
target_metadata = Base.metadata
url = config.attributes.get("url") or Settings().database_url


def run_migrations():
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine = make_engine(url)
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True, render_as_batch=connection.dialect.name == "sqlite")
            with context.begin_transaction():
                context.run_migrations()
        engine.dispose()


run_migrations()
