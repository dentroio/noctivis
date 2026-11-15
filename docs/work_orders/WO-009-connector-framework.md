# WO-009 — Connector framework and model settings

**Status:** Review
**Priority:** P1
**Effort:** L
**Owner:** unassigned
**Services / Areas:** apps/api, apps/web, packages/noctivis

## Problem

The operator cannot choose a model. `docs/ARCHITECTURE.md` expects a supervisor agent, and WO-005 will run one, but nothing records whether that run uses a hosted model or a local one. The console nav is only Investigate and Understand (`apps/web/src/App.tsx`). There is no shared record for a configured external system, so a later VirusTotal-style connection or an agent catalog would each invent their own settings.

The owner asked for a Models page with the same structure as the Clarion AI / LLM screens: a provider list, one default, an add dialog for a local or hosted model, a test prompt, and a place agents will be listed later.

## Decision Context

- Chosen approach: one `connectors` table and `/api/v1/connectors`. The first kind is `llm`. Hosted records store an environment-variable name. Local records store a loopback base URL and use an Ollama-compatible `/api/chat` call. Hosted calls use an OpenAI-compatible chat completion. The Models page is the first screen.
- Alternatives rejected: a one-off Models table. Storing a provider key in Postgres. Copying Clarion's light theme or brand.
- Assumptions: the page uses the Noctivis dark theme. One connector is the default. A test prompt is sent only when the operator submits it. Sample bytes are never included.
- Open decisions: none. Saving a raw key would be a new P0 work order.

## What To Build / Fix

A connector record: id, kind, name, description, enabled, is_default, config JSON, last_checked_at, last_status. `config` for `llm` holds `provider` (`hosted` or `local`), `model`, `base_url` for local, and `api_key_env` for hosted. It does not hold the key.

Routes, all behind the existing local operator check:

- `GET /api/v1/connectors?kind=llm`
- `POST /api/v1/connectors`
- `PATCH /api/v1/connectors/{id}`
- `DELETE /api/v1/connectors/{id}`
- `POST /api/v1/connectors/{id}/test` with a short operator prompt

Only one enabled connector is the default. Disable stops that connector from being used and does not delete it. A local base URL must be `http` or `https` on loopback. A hosted base URL must be `https`. The test call goes only to that configured host.

Console: a Connect section. Its first item is Models. The page matches the reference layout in the dark theme:

- Title and a one-line purpose.
- Add and Disable actions.
- Three summary cards: what this connection does, how many are connected and which is the default, and the next action (test a provider before relying on a hosted model).
- The provider list, with the default marked, the model name, the last test time, and test, edit, and delete actions.
- An add dialog: name, hosted or local, optional description, set as default, model name, base URL for local, environment-variable name for a hosted key.
- A test prompt box that uses the current default.
- A short note that agents will be listed here when WO-010 is built. Do not invent agent rows.

## Expected Change Surface

- Expected: `packages/noctivis` connector model, API routes, a migration, `apps/web` Connect / Models page.
- Tests: create a local provider, reject a non-loopback local URL, reject a stored raw key, one default, test route does not call a process with the sample, unauthenticated requests fail.
- Docs/status: README, `docs/status.md`, this Work Order.

## Out Of Scope

- Running an investigation with the selected model (WO-005).
- The agent catalog (WO-010).
- VirusTotal or any other external system (WO-011).
- A policy gateway (WO-002). The test prompt is an operator action, not a tool call by a model.

## Do NOT Change

- Model text never authorizes a tool call.
- Sample bytes are not sent to a model in this Work Order.
- Samples are not executed.
- The listener stays on loopback.
- Do not store a provider key in source, fixtures, or Postgres.

## Acceptance Criteria

1. The operator can add a local model and a hosted model, mark one default, disable it, and delete it.
2. The hosted record stores the environment-variable name and not the key.
3. A test prompt returns the provider's reply, or a visible error when the provider is unreachable.
4. `pytest -q` passes. `npm run typecheck` and `npm run build` in `apps/web` pass.

## Validation Plan

- Automated: `pytest -q`. `cd apps/web && npm run typecheck && npm run build`.
- Manual: add a local provider pointed at a loopback model, send one test prompt, and confirm the Models page shows it as default.
- Evidence to include: the test name that rejects a stored key, and the manual prompt result.

## Execution

- **Branch:** `wo/009-connector-framework`
- **Risk tier:** P1. Raise to P0 before implementation if raw provider keys will be stored.
- **Pre-PR / pre-merge gate:** `pytest -q` and `cd apps/web && npm run typecheck && npm run build`
- **Depends on:** WO-001 for the Postgres table. The page can be reviewed before WO-005.
- **Human verification required:** Yes
- **Reviewer / approver:** repository owner
- **Project status record:** `docs/status.md`
- **Other status surfaces to reconcile:** none

## Closeout

- Verification evidence: `pytest -q` — 11 passed, including `test_model_provider_round_trip_and_rejects_a_stored_key`. That test kept one default, rejected a stored key, rejected a non-loopback local URL, returned 401 without a session, and a loopback test prompt returned `model reply` without sample bytes. `npm run typecheck` and `npm run build` in `apps/web` passed. The console check is still for the owner.
- Follow-ons filed: WO-010, WO-011
- Residual risks: a hosted test prompt leaves the workstation when the operator sends it. The default model is not used by an investigation until WO-005.
- Docs/status updated: README, `docs/status.md`, this Work Order.
- Status surfaces reconciled: `docs/status.md` lists WO-009 under Review.
- Summary metadata reviewed: focus in `docs/status.md`.
- Planning-only change? No
