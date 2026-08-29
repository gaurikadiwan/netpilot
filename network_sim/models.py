"""Simulated network inventory.

Deliberately simple, deliberately labelled as simulated (see README). The
point isn't to model real telco hardware -- it's to have a realistic-shaped
dataset that the MCP tools can inspect and detect drift in.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC)


class NetworkNode(Base):
    """A single simulated network element (e.g. a gNB, router, or gateway)."""

    __tablename__ = "network_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    site: Mapped[str] = mapped_column(String(64), index=True)
    node_type: Mapped[str] = mapped_column(String(32))  # e.g. "gNB", "router", "gateway"
    status: Mapped[str] = mapped_column(String(16), default="healthy")  # healthy | degraded | down
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    configs: Mapped[list[NodeConfig]] = relationship(back_populates="node", cascade="all, delete-orphan")


class NodeConfig(Base):
    """A config snapshot for a node. `is_baseline=True` marks the approved config."""

    __tablename__ = "node_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("network_nodes.id"))
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(String(256))
    is_baseline: Mapped[bool] = mapped_column(default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    node: Mapped[NetworkNode] = relationship(back_populates="configs")
