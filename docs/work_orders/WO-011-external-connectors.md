# WO-011 — External system connectors

**Status:** Draft
**Priority:** P1
**Effort:** L
**Owner:** unassigned
**Services / Areas:** apps/api, apps/web, packages/noctivis

## Problem

The owner wants Noctivis to connect to outside systems, with VirusTotal named as the example. There is no connector kind for that. A direct VirusTotal client in the API would skip the framework from WO-009 and would decide, on its own, what sample data leaves the workstation.

## Decision Context

- Chosen approach: not chosen. This Work Order is not ready to implement.
- Recommended approach: a new connector kind, `external`, stored through the WO-009 connector API. The first system is a hash lookup. The request sends the SHA-256 only. The Connect section gains a Connections item using the same list, default, test, and disable pattern as Models.
- Alternatives rejected: uploading sample bytes to a third party in this Work Order. A separate settings stack for each vendor.
- Assumptions: the operator turns a connection on. A model cannot open the connection by itself.
- Open decisions: which system is first if it is not VirusTotal, the vendor request shape, rate limits, and what the console shows from the reply. Sending more than the hash is a different, higher-risk decision and is not part of this draft.

## What To Build / Fix

Register one external connector kind. The operator sets a name, the system, and the environment-variable name for that system's key. Test runs a hash lookup for a SHA-256 the operator supplies, or for a sample already stored in Noctivis. The result is shown on the connection. The sample file is not part of the request.

The Connections page lists these connectors with status, last check, test, edit, and delete. It does not list models or agents.

## Expected Change Surface

- Expected: connector kind `external`, one vendor client, Connections page.
- Tests: request body contains the hash and not the file bytes, missing key fails closed, unauthenticated requests fail.
- Docs/status: README caveat for data that leaves the workstation, `docs/status.md`, this Work Order.

## Out Of Scope

- Model providers (WO-009).
- Agent runs (WO-005) and the agent catalog (WO-010).
- Any connector that receives sample bytes.
- Automatic lookups on upload.

## Do NOT Change

- Sample bytes stay on this workstation for this Work Order.
- A model response cannot enable a connector or send a lookup.
- Samples are not executed.
- Provider keys are not stored in source or Postgres.

## Acceptance Criteria

1. The operator can add one external hash-lookup connection, test it with a SHA-256, and see the reply or a clear failure.
2. The outbound request does not contain the sample file.
3. Quality gate passes.

## Validation Plan

- Automated: `pytest -q` against a fake vendor server. `cd apps/web && npm run typecheck && npm run build`.
- Manual: test one stored sample's hash and confirm the Connections page shows the result.
- Evidence to include: the captured request body showing only the hash.

## Execution

- **Branch:** `wo/011-external-connectors`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q` and `cd apps/web && npm run typecheck && npm run build`
- **Depends on:** WO-009
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
