from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mcp_server.config import settings
from network_sim.models import Base


def _connect_args(database_url: str) -> dict:
    # SQLite needs this flag when used from multiple threads (the MCP server
    # and tests each open their own connections); other backends don't.
    return {"check_same_thread": False} if database_url.startswith("sqlite") else {}


engine = create_engine(settings.database_url, connect_args=_connect_args(settings.database_url))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
