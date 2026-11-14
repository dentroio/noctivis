# NOCTIVIS

**Understand. Investigate. Defend.**

NOCTIVIS is an early-stage, modular foundation for an agentic security intelligence platform. The long-term architecture includes binary intelligence, vulnerability research, malware intelligence, threat hunting, exposure analysis, and defensive engineering.

> **Current status:** Foundation scaffold, not a functioning autonomous reverse-engineering system. Ghidra, LangGraph, persistent storage, sandbox execution, and authentication are planned but **not implemented**.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn main:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for the interactive API.

The operator console lives in `apps/web` and uses the local `@sgerhart/ux-framework` package. Until that package is published, its checkout must sit beside this repo at `github/sgerhart/ux-framework` (the `file:` dependency in `apps/web/package.json`).

```bash
cd apps/web
npm install
npm run dev
```

Open http://127.0.0.1:5173. The dev server proxies `/api` and `/health` to the API on 127.0.0.1:8000. Both bind to loopback. The console has no sign-in.

Work is tracked with the [Work Order Protocol](https://github.com/dentroio/work-order-protocol). Read `AGENT_PROCESS.md`, then `docs/status.md`.

```bash
pytest -q
```

## Current endpoints

- `GET /health`
- `GET /api/v1/capabilities`
- `POST /api/v1/binaries` — bounded, non-executing format triage
- `GET /api/v1/binaries`
- `POST /api/v1/investigations` — creates a draft investigation
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{id}`

## Security caveats

The MVP uses in-memory state and has no authentication. Run only on loopback for development. Do not expose to a network or upload sensitive/untrusted artifacts until authentication, persistence, isolation, and malware-safe storage have been implemented. Uploads are deleted after metadata extraction. No binary execution occurs.

## Planned phases

1. Persistent PostgreSQL investigation and evidence models, auth, policy gateway.
2. Ghidra headless static analysis worker, immutable artifact store.
3. LangGraph bounded orchestration and traceable findings.
4. Hypervisor-isolated dynamic analysis with approvals.
5. Additional capability packages and cross-domain correlation.

See `docs/ARCHITECTURE.md` and `docs/ROADMAP.md`.
