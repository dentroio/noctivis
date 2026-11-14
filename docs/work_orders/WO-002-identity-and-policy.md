# WO-002 — Identity and policy

**Status:** Draft
**Priority:** P0
**Effort:** L
**Owner:** unassigned
**Services / Areas:** apps/api, apps/web

## Problem

The API and console have no authentication. `docs/ARCHITECTURE.md` requires a gateway that enforces identity, RBAC, and tool policy independent of model output. The console states this gap on every page rather than showing a fake login.

## Decision Context

- Chosen approach: not chosen.
- Alternatives rejected: a demo login in the console. That would look like access control and is forbidden by `AGENT_PROCESS.md`.
- Assumptions: loopback-only development continues until this Work Order is accepted.
- Open decisions: identity provider, role ladder (`viewer`, `analyst`, `admin` or a different set), where session tokens are stored, and how the tool gateway denies calls.

## What To Build / Fix

Add real authentication and a default-deny policy check for privileged actions. Unauthorized requests fail. Audit events are stored. The console uses the UX framework `AuthProvider` only after the API can answer login and current-user requests.

## Expected Change Surface

- Expected: API auth dependencies, policy checks, console sign-in, audit records.
- Tests: denied unauthenticated requests, allowed authorized requests, audit event written.
- Docs/status: README security caveats, `docs/status.md`.

## Out Of Scope

- Persistent product data (WO-001), except whatever audit storage this Work Order requires.
- Sample execution policy beyond "still denied" (WO-007).

## Do NOT Change

- Do not ship a username form that accepts any password.
- Do not execute uploaded samples.
- Do not bind development servers to a non-loopback address as part of this work unless the acceptance criteria explicitly include a locked-down deployment.

## Acceptance Criteria

1. A request without a valid session is denied for every route that requires one.
2. An authorized session can perform the allowed action, and an audit event is recorded.
3. Quality gate passes.

## Validation Plan

- Automated: `pytest -q` covering allow and deny.
- Manual: sign in through the console and confirm a denied route stays denied for a lower role.
- Evidence to include: the denied request and the audit record.

## Execution

- **Branch:** `wo/002-identity-and-policy`
- **Risk tier:** P0
- **Pre-PR / pre-merge gate:** `pytest -q` and `cd apps/web && npm run typecheck && npm run build`
- **Depends on:** WO-001 for durable audit storage, unless this Work Order explicitly chooses a smaller audit store.
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
