"""network_inventory -- read-only tool.

Lists nodes in the simulated network, optionally filtered by site and/or
status. Requires the `read` scope.
"""

from __future__ import annotations

from pydantic import BaseModel

from mcp_server.audit import audit_call
from mcp_server.auth import CallerContext, Scope, require_scope
from network_sim.database import get_session
from network_sim.models import NetworkNode

REQUIRED_SCOPE = Scope.READ


class NodeSummary(BaseModel):
    name: str
    site: str
    node_type: str
    status: str


def network_inventory(
    ctx: CallerContext,
    site: str | None = None,
    status: str | None = None,
) -> list[NodeSummary]:
    require_scope(ctx, REQUIRED_SCOPE)

    with audit_call(
        tool="network_inventory",
        scope_required=REQUIRED_SCOPE.value,
        arguments={"site": site, "status": status},
    ) as record:
        with get_session() as session:
            query = session.query(NetworkNode)
            if site:
                query = query.filter(NetworkNode.site == site)
            if status:
                query = query.filter(NetworkNode.status == status)
            nodes = query.order_by(NetworkNode.name).all()

            results = [
                NodeSummary(name=n.name, site=n.site, node_type=n.node_type, status=n.status)
                for n in nodes
            ]

        record.result_summary = f"{len(results)} node(s) matched"
        return results
