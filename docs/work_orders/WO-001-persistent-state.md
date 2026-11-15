# WO-001 — Persistent investigation state

**Status:** Review
**Priority:** P1
**Effort:** L
**Owner:** unassigned
**Services / Areas:** apps/api, packages/noctivis

## Problem

Investigations and classified samples disappear when the API process restarts. `INVESTIGATIONS` and `BINARIES` in `apps/api/main.py` are in-memory dictionaries. The architecture target is PostgreSQL as the source of truth (`docs/ARCHITECTURE.md`).

## Decision Context

- Chosen approach: PostgreSQL via `NOCTIVIS_DATABASE_URL`, with versioned SQL files in `packages/noctivis/migrations` applied on connection. Only the records the API already stores are tables: binary metadata and investigations. `findings` stays a JSON field on the investigation row. Sessions stay in memory.
- Alternatives rejected: an ORM and a findings, task, evidence, audit, or approval table in this Work Order. SQLite as a stand-in for PostgreSQL.
- Assumptions: metadata is persisted before sample bytes. Bytes stay deleted after classification until WO-003. The loopback database password in `docker-compose.yml` is a local placeholder.
- Open decisions: none.

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

- Verification evidence: `pytest -q` — 7 passed, including `test_investigation_survives_a_new_database_connection`. A second API process, given the same `NOCTIVIS_DATABASE_URL`, reloaded the investigation created by the first process (`objective` and `binary_id` matched). On 2026-11-14 the running API on 127.0.0.1:8000 stored investigation `57149b27-99b1-4df5-8d3a-7f071b5a4a45` (“Confirm this investigation survives an API restart”) against `restart-check.elf`, was restarted, and returned that same record. The console reload is still for the owner.
- Follow-ons filed: sample bytes remain WO-003. Findings as their own records remain WO-006. Sessions and policy remain WO-002.
- Residual risks: re-uploading the same bytes still replaces the display label. Sessions still end when the API process stops. The development database password is a local placeholder in `docker-compose.yml`.
- Docs/status updated: README storage steps, `docs/ARCHITECTURE.md`, `docs/status.md`, this Work Order.
- Status surfaces reconciled: `docs/status.md` lists WO-001 under Review.
- Summary metadata reviewed: focus and phase in `docs/status.md`.
- Planning-only change? No
