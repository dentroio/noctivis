# WO-008 — Operator console

**Status:** Review
**Priority:** P1
**Effort:** M
**Owner:** repository owner
**Services / Areas:** apps/web, apps/api

## Problem

The platform has an API and no way to operate it. `docs/ARCHITECTURE.md` lists a web console as the experience surface, and `docs/ROADMAP.md` previously tracked only backend phases. An operator cannot classify a sample, open an investigation, or see which capabilities exist without hand-written HTTP calls.

The API also has no list routes. `GET /api/v1/investigations/{id}` requires an id the caller must already know.

## Decision Context

- Chosen approach: a Vite + React console on `@sgerhart/ux-framework`, talking to the existing API through a loopback dev proxy. List routes return the in-memory records. The upload response gains a display `label` that is the file's base name.
- Alternatives rejected: a demo login. The API has no identity, and a form that accepts any password would look like access control. Auth waits for WO-002. Also rejected: opening CORS on the API. The console and API meet only through the Vite proxy on 127.0.0.1.
- Assumptions: the UX framework checkout stays at `github/sgerhart/ux-framework`, linked with a `file:` dependency, until that package is published.
- Open decisions: none for this slice.

## What To Build / Fix

- `GET /api/v1/binaries` and `GET /api/v1/investigations`.
- Upload records include `label`. A path in the client filename is reduced to its base name and is never used as a filesystem path.
- `apps/web` console using the framework shell, page header, table, and loading / empty / error states.
- Pages: Overview, Investigations, investigation detail, Binaries, Capabilities.
- An operator can upload a sample and create an investigation from the console.
- A persistent banner states that the console has no sign-in and that samples are not executed.
- Nav groups follow the work an operator is doing: Investigate and Understand.

## Expected Change Surface

- Expected: `apps/api/main.py`, `apps/web/**`, `tests/test_api.py`, README, architecture "not yet implemented" line.
- Tests: list routes and label path stripping.
- Docs/status: README run instructions, `docs/status.md`, this Work Order.

## Out Of Scope

- Persistence, authentication, artifact retention, Ghidra, orchestration, findings reports, dynamic execution (WO-001 through WO-007).
- Publishing `@sgerhart/ux-framework`.
- A deployment of the built console. `npm run build` only proves the bundle compiles.
- Pagination, sorting, and a work-order board inside the product.

## Do NOT Change

- Uploaded bytes are deleted after classification. Nothing executes them.
- `dynamic_execution: true` is still rejected.
- Existing success behavior of `POST /api/v1/binaries` and `POST /api/v1/investigations`.
- The console must not gain a login form in this Work Order.

## Acceptance Criteria

1. `GET /api/v1/binaries` and `GET /api/v1/investigations` return the records created by the existing POST routes.
2. An upload whose filename contains a directory segment stores `label` as the base name, with no slash.
3. `http://127.0.0.1:5173` renders the framework shell and the five pages above, including loading, empty, and error states.
4. From that origin, an operator can upload a sample and create an investigation, then open the investigation.
5. The page states that there is no sign-in and that the sample is not executed.
6. `pytest -q` passes. `npm run typecheck` and `npm run build` in `apps/web` pass.

## Validation Plan

- Automated: `pytest -q`. `cd apps/web && npm run typecheck && npm run build`.
- Manual: start the API on 127.0.0.1:8000 and the console on 127.0.0.1:5173. Upload a small ELF-header sample, create an investigation, open it, and confirm the banner and the empty findings state.
- Evidence to include: pytest result, typecheck and build result, and the manual path.

## Execution

- **Branch:** `wo/008-operator-console` (implemented on `main` at the owner's request to start the project)
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q` and `cd apps/web && npm run typecheck && npm run build`
- **Depends on:** none
- **Human verification required:** Yes
- **Reviewer / approver:** repository owner
- **Project status record:** `docs/status.md`
- **Other status surfaces to reconcile:** `docs/ROADMAP.md` points here and does not track status itself

## Closeout

- Verification evidence: `pytest -q` — 5 passed. `npm run typecheck` and `npm run build` in `apps/web` passed. Headless Chrome against http://127.0.0.1:5173 uploaded an ELF-header sample, listed it as ELF, created an investigation, opened the detail page (`Not executed`, `No findings yet`), opened Capabilities (`Does not execute`), and showed the error state for an unknown investigation id. Desktop control was not available, so this was not a click-through on the owner's screen.
- Follow-ons filed: WO-001 through WO-007 remain the backlog. No new Work Order for pagination.
- Residual risks: records vanish on API restart. Re-uploading the same bytes replaces the display label. The `file:` dependency requires the UX framework checkout beside this repo. The sidebar starts open, so a narrow window is cramped until it is collapsed.
- Docs/status updated: README, `docs/ARCHITECTURE.md`, `docs/status.md`, `docs/ROADMAP.md`.
- Status surfaces reconciled: `docs/status.md` lists WO-008 under Review. `docs/ROADMAP.md` does not track status.
- Summary metadata reviewed: focus, phase, and blocked fields in `docs/status.md`.
- Planning-only change? No
