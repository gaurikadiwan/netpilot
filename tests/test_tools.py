from __future__ import annotations


def test_list_tools_requires_auth(client):
    resp = client.get("/mcp/tools")
    assert resp.status_code == 401


def test_list_tools_rejects_bad_token(client):
    resp = client.get("/mcp/tools", headers={"Authorization": "Bearer wrong-token"})
    assert resp.status_code == 401


def test_list_tools_returns_registered_tools(client, auth_headers):
    resp = client.get("/mcp/tools", headers=auth_headers)
    assert resp.status_code == 200
    names = {tool["name"] for tool in resp.json()}
    assert names == {"network_inventory", "config_validate"}


def test_network_inventory_returns_all_nodes(client, auth_headers):
    resp = client.post("/mcp/tools/network_inventory/call", headers=auth_headers, json={})
    assert resp.status_code == 200
    nodes = resp.json()
    assert len(nodes) == 15  # 3 sites x 5 nodes, from seed()


def test_network_inventory_filters_by_site(client, auth_headers):
    resp = client.post(
        "/mcp/tools/network_inventory/call",
        headers=auth_headers,
        json={"site": "BNE-01"},
    )
    assert resp.status_code == 200
    nodes = resp.json()
    assert len(nodes) == 5
    assert all(n["site"] == "BNE-01" for n in nodes)


def test_network_inventory_filters_by_status(client, auth_headers):
    resp = client.post(
        "/mcp/tools/network_inventory/call",
        headers=auth_headers,
        json={"status": "degraded"},
    )
    assert resp.status_code == 200
    nodes = resp.json()
    # seed() injects exactly 3 drift cases, each marking its node "degraded"
    assert len(nodes) == 3
    assert all(n["status"] == "degraded" for n in nodes)


def test_config_validate_detects_known_drift(client, auth_headers):
    # seed() drifts node index 2 (BNE-01-gateway-002)'s firmware_version
    resp = client.post(
        "/mcp/tools/config_validate/call",
        headers=auth_headers,
        json={"node_id": 3},  # ids are 1-indexed
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["drifted"] is True
    assert any(d["key"] == "firmware_version" for d in result["drift"])


def test_config_validate_clean_node_has_no_drift(client, auth_headers):
    resp = client.post(
        "/mcp/tools/config_validate/call",
        headers=auth_headers,
        json={"node_id": 1},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["drifted"] is False
    assert result["drift"] == []


def test_config_validate_unknown_node_returns_422(client, auth_headers):
    resp = client.post(
        "/mcp/tools/config_validate/call",
        headers=auth_headers,
        json={"node_id": 9999},
    )
    assert resp.status_code == 422


def test_unknown_tool_returns_404(client, auth_headers):
    resp = client.post("/mcp/tools/does_not_exist/call", headers=auth_headers, json={})
    assert resp.status_code == 404
