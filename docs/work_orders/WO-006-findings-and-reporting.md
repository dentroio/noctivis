# WO-006 — Findings and reporting

**Status:** Draft
**Priority:** P1
**Effort:** M
**Owner:** unassigned
**Services / Areas:** packages/noctivis, apps/api, apps/web

## Problem

`Investigation.findings` is an untyped list and the console has no findings to show. The architecture requires every claim to link to stored evidence, with a review state and a Markdown or JSON report.

## Decision Context

- Chosen approach: not chosen.
- Alternatives rejected: none yet.
- Assumptions: findings are hypotheses until a person marks them reviewed.
- Open decisions: the finding schema, review states, and whether the report is generated on demand or stored.

## What To Build / Fix

Replace free-form finding dicts with a structured finding that cites evidence. The console lists findings for an investigation. An export returns Markdown and JSON in which every claim links to stored evidence.

## Expected Change Surface

- Expected: finding model, report route, investigation detail page.
- Tests: a finding without evidence is rejected; a report contains the citation.
- Docs/status: `docs/status.md`.

## Out Of Scope

- Producing the evidence itself (WO-004, WO-005).
- Changing who is allowed to mark a finding reviewed (WO-002), beyond a single local reviewer if WO-002 is not done.

## Do NOT Change

- The console must not present a model hypothesis as a confirmed result.

## Acceptance Criteria

1. A finding cannot be stored without an evidence reference.
2. The JSON and Markdown reports include that reference.
3. The investigation page lists the finding and its review state.
4. Quality gate passes.

## Validation Plan

- Automated: `pytest -q` and `cd apps/web && npm run typecheck && npm run build`.
- Manual: open an investigation with one finding and export the report.
- Evidence to include: the report excerpt and the evidence id.

## Execution

- **Branch:** `wo/006-findings-and-reporting`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q` and the console typecheck and build
- **Depends on:** WO-005 for real evidence. A fixture evidence row is allowed if the schema is what this Work Order accepts.
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
