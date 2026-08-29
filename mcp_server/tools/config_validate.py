"""config_validate -- read-only tool.

Compares a node's current config values against its recorded baseline and
reports any drift. Requires the `read` scope -- this only inspects state,
it never modifies it.
"""

from __future__ import annotations

from pydantic import BaseModel

from mcp_server.audit import audit_call
from mcp_server.auth import CallerContext, Scope, require_scope
from network_sim.database import get_session
from network_sim.models import NetworkNode, NodeConfig

REQUIRED_SCOPE = Scope.READ


class DriftEntry(BaseModel):
    key: str
    baseline_value: str
    current_value: str


class ConfigValidateResult(BaseModel):
    node_name: str
    drifted: bool
    drift: list[DriftEntry]


def config_validate(ctx: CallerContext, node_id: int) -> ConfigValidateResult:
    require_scope(ctx, REQUIRED_SCOPE)

    with audit_call(
        tool="config_validate",
        scope_required=REQUIRED_SCOPE.value,
        arguments={"node_id": node_id},
    ) as record:
        with get_session() as session:
            node = session.get(NetworkNode, node_id)
            if node is None:
                raise ValueError(f"No node with id={node_id}")

            baseline = {
                c.key: c.value
                for c in session.query(NodeConfig).filter_by(node_id=node_id, is_baseline=True)
            }
            current = {
                c.key: c.value
                for c in session.query(NodeConfig).filter_by(node_id=node_id, is_baseline=False)
            }

            drift = [
                DriftEntry(key=key, baseline_value=baseline[key], current_value=current[key])
                for key in baseline
                if baseline.get(key) != current.get(key)
            ]

            result = ConfigValidateResult(
                node_name=node.name,
                drifted=len(drift) > 0,
                drift=drift,
            )

        record.result_summary = (
            f"{len(drift)} drifted key(s)" if drift else "no drift detected"
        )
        return result
