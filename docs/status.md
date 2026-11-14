# Project status

**Last updated:** 2026-11-13
**Focus:** Review the operator console (WO-008)
**Phase:** Foundation. In-memory API, no authentication, samples are classified and deleted.
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
| [WO-001](work_orders/WO-001-persistent-state.md) | Persistent investigation state | P1 |
| [WO-002](work_orders/WO-002-identity-and-policy.md) | Identity and policy | P0 |
| [WO-003](work_orders/WO-003-artifact-storage.md) | Immutable artifact storage | P1 |
| [WO-004](work_orders/WO-004-ghidra-worker.md) | Ghidra static analysis worker | P1 |
| [WO-005](work_orders/WO-005-agent-orchestration.md) | Bounded agent orchestration | P1 |
| [WO-006](work_orders/WO-006-findings-and-reporting.md) | Findings and reporting | P1 |
| [WO-007](work_orders/WO-007-dynamic-sandbox.md) | Dynamic sandbox | P0 |

WO-001 through WO-007 are drafts. They are not authorization to implement.

## Review

| WO | Title | Risk |
| --- | --- | --- |
| [WO-008](work_orders/WO-008-operator-console.md) | Operator console | P1 |

## Complete

None.

## Recently changed

- Adopted the Work Order Protocol: process, template, status record, and Cursor rule.
- WO-008 operator console is implemented and waiting for review. List routes and a display label were added to the API. The console is a local shell on the UX framework.
