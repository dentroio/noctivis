# WO-001 — Persistent investigation state

**Status:** Draft
**Priority:** P1
**Effort:** L
**Owner:** unassigned
**Services / Areas:** apps/api, packages/noctivis

## Problem

Investigations and classified samples disappear when the API process restarts. `INVESTIGATIONS` and `BINARIES` in `apps/api/main.py` are in-memory dictionaries. The architecture target is PostgreSQL as the source of truth (`docs/ARCHITECTURE.md`).

## Decision Context

- Chosen approach: not chosen. This Work Order is not ready to implement.
- Alternatives rejected: none yet.
- Assumptions: metadata is persisted before sample bytes. Bytes stay deleted after classification until WO-003.
- Open decisions: migration tool, local PostgreSQL setup, which of task, evidence, finding, audit, and approval tables land in this Work Order versus later ones.

## What To Build / Fix

Replace the in-memory dictionaries with a migrated PostgreSQL schema for the records this API already stores: binary metadata and investigations. Restarting the API must retain them.

Do not design the full future schema in code until the open decisions above are accepted.

## Expected Change Surface

- Expected: `apps/api`, `packages/noctivis`, new migration files, tests that restart or reconnect and still read the row.
- Tests: migration and retention tests.
- Docs/status: `docs/status.md`, this Work Order, README storage caveat.

## Out Of Scope

- Authentication and RBAC (WO-002).
- Storing sample bytes (WO-003).
- Workers, Ghidra, and agent orchestration (WO-004, WO-005).

## Do NOT Change

- Uploaded samples are not executed.
- `dynamic_execution` stays denied.
- The console contract in WO-008, except where a persistence change requires the same JSON fields.

## Acceptance Criteria

1. Creating an investigation, restarting the API, and reading it back returns the same record.
2. Migration tests pass against a disposable database.
3. Quality gate passes.

## Validation Plan

- Automated: `pytest -q`, including a retention test.
- Manual: create an investigation in the console, restart the API, reload the investigation.
- Evidence to include: test name and the restart check.

## Execution

- **Branch:** `wo/001-persistent-state`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q`
- **Depends on:** none
- **Human verification required:** Yes
- **Reviewer / approver:** repository owner
- **Project status record:** `docs/status.md`
- **Other status surfaces to reconcile:** none

## Closeout

- Verification evidence:
- Follow-ons filed:
- Residual risks:
- Docs/status updated:
- Status surfaces reconciled:
- Summary metadata reviewed:
- Planning-only change? No
