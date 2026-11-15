# Project status

**Last updated:** 2026-11-15
**Focus:** Review persistent state, artifact storage, and connectors (WO-001, WO-003, WO-009)
**Phase:** Foundation. Binary metadata, investigations, and Ghidra evidence are in PostgreSQL. Sample bytes are stored by hash and are not executed. Sessions stay in memory.
**Blocked:** none

Work Orders are the source for scope and closeout. This file is the only project status board. `docs/ROADMAP.md` is product direction, not a second list of active work.

Protocol: [Work Order Protocol](https://github.com/dentroio/work-order-protocol), adoption level 2. Process: `AGENT_PROCESS.md`.

## Status surfaces

| Surface | Role | Updated when |
| --- | --- | --- |
| `docs/work_orders/` | Source. Scope, acceptance, closeout. | A Work Order is drafted, accepted, or closed. |
| `docs/status.md` | What is open, active, blocked, in review, and complete. | Every closeout, and when focus changes. |
| `docs/ROADMAP.md` | Product direction only. | When the phase story changes. |

## In progress

None.

## Open

| WO | Title | Risk |
| --- | --- | --- |
| [WO-002](work_orders/WO-002-identity-and-policy.md) | Identity and policy | P0 |
| [WO-005](work_orders/WO-005-agent-orchestration.md) | Bounded agent orchestration | P1 |
| [WO-006](work_orders/WO-006-findings-and-reporting.md) | Findings and reporting | P1 |
| [WO-007](work_orders/WO-007-dynamic-sandbox.md) | Dynamic sandbox | P0 |
| [WO-010](work_orders/WO-010-agent-catalog.md) | Agent catalog | P2 |
| [WO-011](work_orders/WO-011-external-connectors.md) | External system connectors | P1 |

WO-002, WO-005 through WO-007, WO-010, and WO-011 are drafts. They are not authorization to implement.

## Review

| WO | Title | Risk |
| --- | --- | --- |
| [WO-001](work_orders/WO-001-persistent-state.md) | Persistent investigation state | P1 |
| [WO-003](work_orders/WO-003-artifact-storage.md) | Immutable artifact storage | P1 |
| [WO-009](work_orders/WO-009-connector-framework.md) | Connector framework and model settings | P1 |

## Complete

| WO | Title | Risk |
| --- | --- | --- |
| [WO-004](work_orders/WO-004-ghidra-worker.md) | Ghidra static analysis worker | P1 |
| [WO-008](work_orders/WO-008-operator-console.md) | Operator console | P1 |

## Recently changed

- WO-004 accepted. The owner confirmed the fixture inventory and the decompilation of `main` on the investigation page. The sample was not executed.
- WO-008 operator console accepted. The local operator sign-in and the dark theme shipped with it.
- WO-001 stores binary metadata and investigations in PostgreSQL. Sessions stay in memory. Waiting on a console restart check.
- WO-003 stores sample bytes by SHA-256. The API still does not execute them.
- WO-004 queues ELF analysis on the Mac. `noctivis-linux` runs Ghidra 11.4.3 and writes the function inventory and one decompilation. The sample is not executed. `noctivis-windows` is reserved for PE.
