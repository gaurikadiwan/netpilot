# NetPilot

An MCP-style infrastructure copilot backend: controlled, permission-scoped
tools an AI assistant can call to inspect a simulated network — without
being able to silently change anything.

This is a **personal portfolio project**. All network data, devices, and
"incidents" are simulated. No real infrastructure is touched.

## Why this exists

Infrastructure/network engineers increasingly want AI assistants that can
answer questions like *"which devices have config drift?"* — but handing
an LLM unrestricted tool access to production infrastructure is a real
risk. NetPilot is a small, honest demonstration of the pattern that makes
that safe: every tool declares an explicit permission level
(`read` / `plan` / `mutate`), mutating actions require a separate
approval token, and every call is audit-logged.

## Status: Milestone 1 — "It runs"

- [x] Simulated network inventory (Postgres)
- [x] `network_inventory` tool (read-only)
- [x] `config_validate` tool (read-only, flags config drift against baseline)
- [x] Token-based auth with per-tool permission scopes
- [x] Structured audit logging
- [ ] Milestone 2 — Kubernetes inspection tool + Terraform plan analysis (kind + LocalStack)
- [ ] Milestone 3 — the one gated `apply_remediation` mutating tool + human approval flow
- [ ] Milestone 4 — CI/CD pipeline, Prometheus metrics, demo

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design.

## Tech stack

| Layer | Choice |
|---|---|
| API | FastAPI |
| DB | PostgreSQL + SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Auth | Bearer token, per-tool scopes |
| Tests | pytest |
| Lint/format | Ruff, Black |

## Tool interface

Tools are transport-agnostic (`mcp_server/tools/base.py`) so this same
registry can be exposed over the real MCP protocol in Milestone 2 without
rewriting tool logic — for now they're callable over a plain HTTP endpoint
so the project is runnable and testable end-to-end today.

## Quickstart

```bash
# 1. Start Postgres
docker compose up -d

# 2. Install deps
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env

# 4. Seed simulated network data
python -m network_sim.seed

# 5. Run the server
uvicorn mcp_server.main:app --reload
```

API docs: http://localhost:8000/docs

## Example calls

```bash
curl -s http://localhost:8000/mcp/tools \
  -H "Authorization: Bearer dev-read-token"

curl -s -X POST http://localhost:8000/mcp/tools/network_inventory/call \
  -H "Authorization: Bearer dev-read-token" \
  -H "Content-Type: application/json" \
  -d '{"site": "brisbane-core", "status": "degraded"}'

curl -s -X POST http://localhost:8000/mcp/tools/config_validate/call \
  -H "Authorization: Bearer dev-read-token" \
  -H "Content-Type: application/json" \
  -d '{"device_id": 3}'
```

## Testing

```bash
pytest -v
```

## Roadmap

See the Status checklist above — Milestones 2–4 add Kubernetes inspection,
Terraform plan analysis, the gated remediation tool, CI/CD, and
observability.

## License

MIT
