# WO-007 — Dynamic sandbox

**Status:** Draft
**Priority:** P0
**Effort:** XL
**Owner:** unassigned
**Services / Areas:** sandbox, apps/api

## Problem

`create_investigation` returns 403 when `dynamic_execution` is true. That denial is the correct behavior until execution happens in a disposable, network-denied machine. `docs/ARCHITECTURE.md` requires hypervisor isolation, explicit approval, resource limits, and teardown.

## Decision Context

- Chosen approach: not chosen. Do not implement from this draft.
- Alternatives rejected: executing a sample in a container on the API host.
- Assumptions: a person approves each run. The network is denied by default.
- Open decisions: hypervisor, image build, approval record, capture format, and how teardown is proven.

## What To Build / Fix

An approved task runs a sample in a disposable VM with no network path, then destroys the VM. The API host still never executes the sample.

## Expected Change Surface

- Expected: approval record, sandbox runner, teardown tests.
- Tests: adversarial isolation tests named in the accepted design.
- Docs/status: `docs/status.md`, README caveat removed only for the approved path.

## Out Of Scope

- Static analysis (WO-004).
- Turning the console's current "not executed" copy off for unapproved investigations.

## Do NOT Change

- Unapproved investigations still cannot set `dynamic_execution`.
- The API process still does not execute sample bytes.

## Acceptance Criteria

1. An unapproved request is denied.
2. An approved run has no network path, and the VM is gone afterward.
3. Adversarial isolation tests pass.

## Validation Plan

- Automated: isolation tests in the accepted plan.
- Manual: approve one run and confirm the VM no longer exists.
- Evidence to include: denial, network-deny check, teardown check.

## Execution

- **Branch:** `wo/007-dynamic-sandbox`
- **Risk tier:** P0
- **Pre-PR / pre-merge gate:** the isolation suite named when this Work Order is accepted
- **Depends on:** WO-002, WO-003
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
