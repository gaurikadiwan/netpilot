"""Tool permission boundaries.

This is the module the whole project exists to demonstrate: every NetPilot
tool declares the minimum scope it needs, and a call is rejected before it
touches any data if the caller's token doesn't hold that scope.

Scopes, low to high privilege:
  read   -- inspect state (inventory, config, metrics)
  plan   -- compute a proposed change without applying it (e.g. a Terraform plan)
  mutate -- apply a change. No tool in Milestone 1 uses this scope; it exists
            now so the permission model doesn't need to change shape later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mcp_server.config import settings


class Scope(str, Enum):
    READ = "read"
    PLAN = "plan"
    MUTATE = "mutate"


class PermissionError(Exception):
    """Raised when a caller's token does not hold a required scope."""


@dataclass(frozen=True)
class CallerContext:
    token: str
    granted_scopes: set[str]

    def has_scope(self, scope: Scope) -> bool:
        return scope.value in self.granted_scopes


def authenticate(token: str) -> CallerContext:
    """Validate a bearer token and return the scopes it's been granted.

    Raises PermissionError on any mismatch. Deliberately does not distinguish
    "unknown token" from "wrong token" in the error message returned to the
    caller, to avoid leaking which one it was -- the distinction is available
    to whoever reads the audit log.
    """
    if token != settings.netpilot_api_token:
        raise PermissionError("Invalid or missing API token.")
    return CallerContext(token=token, granted_scopes=settings.token_scopes)


def require_scope(ctx: CallerContext, scope: Scope) -> None:
    if not ctx.has_scope(scope):
        raise PermissionError(
            f"Token does not hold the '{scope.value}' scope required for this tool."
        )
