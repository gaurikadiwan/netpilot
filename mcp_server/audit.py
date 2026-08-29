"""Structured audit logging.

Every tool call is recorded as a single JSON line: who called it, what scope
it required, what arguments were passed, whether it succeeded, and a short
summary of the result. This is what lets you answer "what did the AI layer
actually do" after the fact, independent of chat history.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from mcp_server.config import settings

logger = logging.getLogger("netpilot.audit")
logger.setLevel(settings.log_level)

_handler = logging.FileHandler(settings.audit_log_path)
_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_handler)


@dataclass
class AuditRecord:
    tool: str
    scope_required: str
    arguments: dict[str, Any]
    status: str = "pending"
    result_summary: str | None = None
    error: str | None = None
    duration_ms: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "timestamp": time.time(),
                "tool": self.tool,
                "scope_required": self.scope_required,
                "arguments": self.arguments,
                "status": self.status,
                "result_summary": self.result_summary,
                "error": self.error,
                "duration_ms": round(self.duration_ms, 2),
                **self.extra,
            }
        )


@contextmanager
def audit_call(tool: str, scope_required: str, arguments: dict[str, Any]) -> Iterator[AuditRecord]:
    """Wrap a tool call: always writes exactly one audit line, success or failure.

    Usage:
        with audit_call("network_inventory", "read", {"site": site}) as record:
            result = do_the_work()
            record.status = "success"
            record.result_summary = f"{len(result)} nodes returned"
    """
    record = AuditRecord(tool=tool, scope_required=scope_required, arguments=arguments)
    start = time.perf_counter()
    try:
        yield record
        if record.status == "pending":
            record.status = "success"
    except Exception as exc:
        record.status = "error"
        record.error = str(exc)
        raise
    finally:
        record.duration_ms = (time.perf_counter() - start) * 1000
        logger.info(record.to_json())
