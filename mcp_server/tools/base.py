"""Tool registry.

Each tool is a plain Python callable with a declared required scope and a
Pydantic model describing its arguments. Keeping the registry independent of
any transport (HTTP today, real MCP protocol in Milestone 2) means the tool
logic itself never has to change when the transport does.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from mcp_server.auth import CallerContext, Scope


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required_scope: Scope
    args_model: type[BaseModel]
    handler: Callable[..., Any]

    def input_schema(self) -> dict:
        return self.args_model.model_json_schema()


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool '{spec.name}' is already registered.")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def list(self) -> list[ToolSpec]:
        return sorted(self._tools.values(), key=lambda t: t.name)

    def call(self, name: str, ctx: CallerContext, args: dict) -> Any:
        spec = self.get(name)
        if spec is None:
            raise KeyError(f"Unknown tool: '{name}'")
        parsed = spec.args_model.model_validate(args)
        return spec.handler(ctx, **parsed.model_dump())
