"""NetPilot server entrypoint.

Exposes the tool registry over plain HTTP for Milestone 1. Milestone 2 wires
the same ToolRegistry up to a real MCP transport -- nothing in tools/ or
auth.py needs to change for that, only this file.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Body, FastAPI, Header, HTTPException
from pydantic import BaseModel

from mcp_server.auth import PermissionError as NetPilotPermissionError
from mcp_server.auth import authenticate
from mcp_server.tools.base import ToolRegistry, ToolSpec
from mcp_server.tools.config_validate import REQUIRED_SCOPE as CONFIG_VALIDATE_SCOPE
from mcp_server.tools.config_validate import config_validate
from mcp_server.tools.network_inventory import REQUIRED_SCOPE as NETWORK_INVENTORY_SCOPE
from mcp_server.tools.network_inventory import network_inventory
from network_sim.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="NetPilot",
    description="MCP-style infrastructure inspection tools with permission "
    "boundaries and audit logging.",
    version="0.1.0",
    lifespan=lifespan,
)


# --- Argument schemas for the tools registered below -----------------------

class NetworkInventoryArgs(BaseModel):
    site: str | None = None
    status: str | None = None


class ConfigValidateArgs(BaseModel):
    node_id: int


registry = ToolRegistry()
registry.register(
    ToolSpec(
        name="network_inventory",
        description="List simulated network nodes, optionally filtered by site/status.",
        required_scope=NETWORK_INVENTORY_SCOPE,
        args_model=NetworkInventoryArgs,
        handler=network_inventory,
    )
)
registry.register(
    ToolSpec(
        name="config_validate",
        description="Check a node's live config against its baseline and report drift.",
        required_scope=CONFIG_VALIDATE_SCOPE,
        args_model=ConfigValidateArgs,
        handler=config_validate,
    )
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {"status": "ready"}


@app.get("/mcp/tools")
def list_tools(authorization: str = Header(default="")) -> list[dict]:
    _authenticate(authorization)
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "required_scope": spec.required_scope.value,
            "input_schema": spec.input_schema(),
        }
        for spec in registry.list()
    ]


@app.post("/mcp/tools/{tool_name}/call")
def call_tool(
    tool_name: str,
    args: dict[str, Any] = Body(default_factory=dict),
    authorization: str = Header(default=""),
) -> Any:
    ctx = _authenticate(authorization)
    try:
        return registry.call(tool_name, ctx, args)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NetPilotPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _authenticate(authorization: str):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return authenticate(token)
    except NetPilotPermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
