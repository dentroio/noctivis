# WO-004 — Ghidra static analysis worker

**Status:** Draft
**Priority:** P1
**Effort:** XL
**Owner:** unassigned
**Services / Areas:** worker, apps/api

## Problem

Classification in `packages/noctivis/triage.py` reads eight header bytes and returns a format name. The capability registry advertises `binary.list_functions` and `binary.decompile`, but nothing implements them. The first vertical slice in `docs/ARCHITECTURE.md` is an ELF function inventory and a decompilation tied to the sample hash.

## Decision Context

- Chosen approach: not chosen.
- Alternatives rejected: running Ghidra inside the API process. The API host must not become an analysis sandbox.
- Assumptions: a separate worker process reads stored bytes and writes results back as evidence.
- Open decisions: how the worker is packaged, which Ghidra version is pinned, queue technology, and where evidence is stored before WO-006.

## What To Build / Fix

An isolated headless worker that, for one stored ELF, records a function inventory and a decompilation. Each result cites the sample SHA-256 and the tool version.

## Expected Change Surface

- Expected: new worker package, a job handoff from the API, evidence records.
- Tests: fixture ELF analyzed in the worker, API host test proves it does not invoke Ghidra.
- Docs/status: capability description, `docs/status.md`.

## Out Of Scope

- Agent selection of which function to decompile (WO-005).
- Dynamic execution (WO-007).
- PE and Mach-O analysis, unless a later amendment adds them.

## Do NOT Change

- The API process does not execute the sample and does not shell out to Ghidra.
- `dynamic_execution` stays denied.

## Acceptance Criteria

1. A known ELF fixture produces a function inventory and a decompilation stored with the sample SHA-256 and Ghidra version.
2. API tests still perform no sample execution.
3. Quality gate passes.

## Validation Plan

- Automated: worker test against the fixture, `pytest -q`.
- Manual: open the investigation in the console and see the inventory once the console has a place to show it.
- Evidence to include: fixture hash, tool version, function count.

## Execution

- **Branch:** `wo/004-ghidra-worker`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q`
- **Depends on:** WO-003
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
