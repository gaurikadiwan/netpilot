"""Seed the simulated network inventory.

Run with: python -m network_sim.seed

Creates ~15 nodes across 3 sites, gives each a baseline config, then
deliberately drifts a handful of them so the config_validate tool has
something real to detect. Everything here is synthetic -- see README.
"""

from __future__ import annotations

import random

from network_sim.database import get_session, init_db
from network_sim.models import NetworkNode, NodeConfig

SITES = ["BNE-01", "SYD-02", "MEL-03"]
NODE_TYPES = ["gNB", "router", "gateway"]

BASELINE_CONFIG = {
    "firmware_version": "24.3.1",
    "max_connections": "512",
    "tls_min_version": "1.2",
    "log_level": "INFO",
}

# (node_index, config_key, drifted_value) -- intentionally introduces drift
DRIFT_CASES = [
    (2, "firmware_version", "23.9.0"),   # rolled-back firmware
    (5, "tls_min_version", "1.0"),        # weakened TLS -- a security-relevant drift
    (9, "log_level", "DEBUG"),            # verbose logging left on in "production"
]


def seed(nodes_per_site: int = 5, seed_value: int = 42) -> None:
    random.seed(seed_value)
    init_db()

    with get_session() as session:
        nodes: list[NetworkNode] = []
        counter = 0
        for site in SITES:
            for _ in range(nodes_per_site):
                node = NetworkNode(
                    name=f"{site}-{NODE_TYPES[counter % len(NODE_TYPES)]}-{counter:03d}",
                    site=site,
                    node_type=NODE_TYPES[counter % len(NODE_TYPES)],
                    status="healthy",
                )
                session.add(node)
                nodes.append(node)
                counter += 1
        session.flush()  # assign ids

        for node in nodes:
            for key, value in BASELINE_CONFIG.items():
                session.add(NodeConfig(node_id=node.id, key=key, value=value, is_baseline=True))
                session.add(NodeConfig(node_id=node.id, key=key, value=value, is_baseline=False))
        session.flush()  # persist configs so they can be queried back below

        for index, key, drifted_value in DRIFT_CASES:
            node = nodes[index]
            current = (
                session.query(NodeConfig)
                .filter_by(node_id=node.id, key=key, is_baseline=False)
                .one()
            )
            current.value = drifted_value
            node.status = "degraded"

    print(f"Seeded {len(nodes)} nodes across {len(SITES)} sites, "
          f"{len(DRIFT_CASES)} with injected config drift.")


if __name__ == "__main__":
    seed()
