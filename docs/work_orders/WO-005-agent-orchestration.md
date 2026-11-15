# WO-005 — Bounded agent orchestration

**Status:** Draft
**Priority:** P1
**Effort:** XL
**Owner:** unassigned
**Services / Areas:** packages/noctivis, apps/api

## Problem

An investigation stores an objective and a `max_tool_calls` budget, then stays in `created`. Nothing selects a function, calls a tool, or records evidence. `docs/ARCHITECTURE.md` requires a supervisor whose output cannot authorize a tool call by itself.

## Decision Context

- Chosen approach: not chosen.
- Alternatives rejected: letting model output call tools directly.
- Assumptions: the policy gateway from WO-002 is the only component that may allow a tool call. Until WO-002 exists, this Work Order cannot be accepted.
- Open decisions: LangGraph versus another graph runtime, checkpoint store, and how a budget exhaustion is shown to the operator.

## What To Build / Fix

A bounded orchestration run for one sample: the supervisor may request a tool, the gateway allows or denies it, and the run stops at `max_tool_calls`. Evidence citations point at stored tool output. Repeating the run on the same fixture is deterministic given the same tool versions.

## Expected Change Surface

- Expected: orchestration package, task records, investigation status transitions.
- Tests: budget stop, denied tool call, cited evidence.
- Docs/status: `docs/status.md`.

## Out Of Scope

- Dynamic execution (WO-007).
- The findings report format (WO-006), beyond storing the citations this run needs.

## Do NOT Change

- Model text never authorizes a tool.
- Samples still do not execute on the API host.

## Acceptance Criteria

1. A fixture investigation finishes within its tool-call budget.
2. A tool request the gateway denies is not executed, and the denial is stored.
3. Quality gate passes.

## Validation Plan

- Automated: `pytest -q` with a fake tool backend.
- Manual: run one investigation from the console and read the cited evidence.
- Evidence to include: budget count and a denied call.

## Execution

- **Branch:** `wo/005-agent-orchestration`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q`
- **Depends on:** WO-002, WO-004, WO-009. The run uses the default model connector. It does not choose a vendor on its own.
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
