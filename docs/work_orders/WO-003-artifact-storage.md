# WO-003 — Immutable artifact storage

**Status:** Draft
**Priority:** P1
**Effort:** L
**Owner:** unassigned
**Services / Areas:** apps/api

## Problem

`upload_binary` in `apps/api/main.py` hashes a sample, classifies the header, and deletes the temp file. Later static analysis has nothing to open. The architecture target is a content-addressed immutable store.

## Decision Context

- Chosen approach: not chosen.
- Alternatives rejected: none yet.
- Assumptions: the API host still does not execute samples. The store holds bytes for a worker to read.
- Open decisions: MinIO versus another object store, size and type limits beyond the current 20 MiB cap, retention, and how a caller retrieves bytes without the API executing them.

## What To Build / Fix

Store sample bytes by SHA-256 after classification. Retrieval returns the bytes and verifies the hash. The API still does not execute the file.

## Expected Change Surface

- Expected: upload path, object storage client, retrieval route, tests with a disposable store.
- Tests: round-trip hash verification, oversize rejection, no process spawn.
- Docs/status: README caveat, `docs/status.md`.

## Out Of Scope

- Ghidra or any analyzer that opens the bytes (WO-004).
- Authentication on the retrieval route (WO-002). Retrieval must not ship on a reachable network before WO-002.

## Do NOT Change

- No sample execution on the API host.
- Temp files created during upload are still removed after the bytes are in the store.

## Acceptance Criteria

1. A stored object can be fetched and its SHA-256 matches the upload.
2. An oversized upload is rejected and not stored.
3. Quality gate passes, and tests do not spawn the sample.

## Validation Plan

- Automated: `pytest -q` against a disposable object store.
- Manual: upload from the console and confirm the sample is still listed after an API restart only if WO-001 is already done. Otherwise document that metadata is still in memory.
- Evidence to include: hash match output.

## Execution

- **Branch:** `wo/003-artifact-storage`
- **Risk tier:** P1
- **Pre-PR / pre-merge gate:** `pytest -q`
- **Depends on:** none for the object store. Durable metadata depends on WO-001.
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
