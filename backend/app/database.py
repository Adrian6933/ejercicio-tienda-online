from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from fastapi import Request


class Base(DeclarativeBase):
    pass


def make_engine(url):
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    options = {"connect_args": {"check_same_thread": False, "timeout": 20}} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_setup(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=20000")

    return engine


def factory(engine):
    return sessionmaker(engine, expire_on_commit=False)


def get_db(request: Request):
    with request.app.state.sessions() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
