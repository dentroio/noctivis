# NOCTIVIS

**Understand. Investigate. Defend.**

NOCTIVIS is an early-stage, modular foundation for an agentic security intelligence platform. The long-term architecture includes binary intelligence, vulnerability research, malware intelligence, threat hunting, exposure analysis, and defensive engineering.

> **Current status:** Foundation scaffold, not a functioning autonomous reverse-engineering system. One local operator can sign in. Binary metadata and investigations survive an API restart in PostgreSQL. Sample bytes are stored by SHA-256. Ghidra, LangGraph, and sandbox execution are **not implemented**.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d
export NOCTIVIS_DATABASE_URL='postgresql://noctivis:test%20database%20password@127.0.0.1:5433/noctivis'
export NOCTIVIS_ARTIFACT_DIR="$PWD/var/artifacts"
uvicorn main:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000
```

`docker compose` starts PostgreSQL on 127.0.0.1:5433 so it does not take the usual Postgres port. The password above is the local placeholder from `docker-compose.yml`, not a production credential. Set `NOCTIVIS_OPERATOR_NAME` and `NOCTIVIS_OPERATOR_PASSWORD` before starting the API. When the operator password is unset, the process prints a password once at startup. Sessions live in memory and end when the API stops.

Open http://127.0.0.1:8000/docs for the interactive API.

The operator console lives in `apps/web` and uses the local `@sgerhart/ux-framework` package. Until that package is published, its checkout must sit beside this repo at `github/sgerhart/ux-framework` (the `file:` dependency in `apps/web/package.json`).

```bash
cd apps/web
npm install
npm run dev
```

Open http://127.0.0.1:5173 and sign in. The dev server proxies `/api` and `/health` to the API on 127.0.0.1:8000. Both bind to loopback.

The API expects one local operator, `NOCTIVIS_DATABASE_URL`, and `NOCTIVIS_ARTIFACT_DIR`. Sessions live in memory and end when the API stops. Binary metadata and investigations remain in PostgreSQL. Sample bytes remain in the artifact directory, addressed by SHA-256.

Static analysis does not run on this Mac. The Mac queues a job. A Linux guest on Proxmox claims that job and runs Ghidra 11.4.3. A Windows guest on the same Proxmox backend is reserved for PE analysis. PostgreSQL stays on 127.0.0.1. The Mac opens the tunnel the guest uses:

```bash
ssh -N -R 127.0.0.1:5433:127.0.0.1:5433 noctivis@192.168.100.106
```

On the guest, with `GHIDRA_HOME` and `JAVA_HOME` set, `python -m noctivis --once` claims one job. The sample is imported for decompilation and is not executed.

Work is tracked with the [Work Order Protocol](https://github.com/dentroio/work-order-protocol). Read `AGENT_PROCESS.md`, then `docs/status.md`.

```bash
pytest -q
```

## Current endpoints

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /health`
- `GET /api/v1/capabilities`
- `GET /api/v1/connectors?kind=llm`
- `POST /api/v1/connectors`
- `PATCH /api/v1/connectors/{id}`
- `DELETE /api/v1/connectors/{id}`
- `POST /api/v1/connectors/{id}/test`
- `POST /api/v1/binaries` — bounded, non-executing format triage
- `GET /api/v1/binaries`
- `GET /api/v1/binaries/{id}/content` — stored bytes, hash-checked, not executed
- `POST /api/v1/investigations` — creates a draft investigation
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{id}`
- `POST /api/v1/investigations/{id}/analysis` — queues Ghidra; the API does not run it
- `GET /api/v1/investigations/{id}/analysis`
- `GET /api/v1/investigations/{id}/evidence`

## Security caveats

One local operator password gates the console and the API. Binary metadata and investigations are in PostgreSQL. Sample bytes are stored by SHA-256 and are not executed. Run only on loopback for development. Do not expose it to a network or upload sensitive or untrusted artifacts until persistent identity, isolation, and a reviewed retention policy exist.

## Planned phases

1. Persistent PostgreSQL investigation and evidence models, auth, policy gateway.
2. Ghidra headless static analysis worker, immutable artifact store.
3. LangGraph bounded orchestration and traceable findings.
4. Hypervisor-isolated dynamic analysis with approvals.
5. Additional capability packages and cross-domain correlation.

See `docs/ARCHITECTURE.md` and `docs/ROADMAP.md`.
