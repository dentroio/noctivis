# WO-004 — Ghidra static analysis worker

**Status:** Complete
**Priority:** P1
**Effort:** XL
**Owner:** unassigned
**Services / Areas:** worker, apps/api

## Problem

Classification in `packages/noctivis/triage.py` reads eight header bytes and returns a format name. The capability registry advertises `binary.list_functions` and `binary.decompile`, but nothing implements them. The first vertical slice in `docs/ARCHITECTURE.md` is an ELF function inventory and a decompilation tied to the sample hash.

## Decision Context

- Chosen approach: the ARM Mac runs the API, the console, PostgreSQL, and the artifact store on loopback. It queues a job. Ghidra runs only in a worker process on a Proxmox guest. The Linux guest analyzes ELF. The Windows guest is reserved for a later PE order. The queue is the `analysis_jobs` table. Evidence is two rows, `function_inventory` and `decompilation`, until WO-006. The pinned analyzer is Ghidra 11.4.3 with JDK 21, because that build includes the Linux x86-64 and Windows x86-64 decompilers.
- Alternatives rejected: running Ghidra inside the API process. Hosting the Linux or Windows guest on this ARM Mac. Ghidra 12.2 on the Mac, whose public build has no Apple Silicon decompiler.
- Assumptions: the operator creates both guests on Proxmox. The guest reaches PostgreSQL through an SSH tunnel, so the database stays bound to loopback. The sample is imported by Ghidra and is not executed.
- Open decisions: none for this order. The Mac opens the database tunnel with `ssh -R 127.0.0.1:5433:127.0.0.1:5433` to the Linux guest, so Postgres stays on loopback. The Proxmox host is `192.168.100.12` (`proxmox-3`). The Linux guest is VM 109, `noctivis-linux`, Ubuntu 26.04.1, DHCP `192.168.100.106`, user `noctivis`. The Windows guest is VM 110, `noctivis-windows`, created stopped with the Windows 11 installer and VirtIO drivers attached.

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

- Verification evidence: `pytest -q` — 13 passed. The API test queues an analysis job and does not launch a process. On `noctivis-linux`, Ghidra 11.4.3 imported fixture `tests/fixtures/add.o` (SHA-256 `58cac356fa052338c5f2cccf107eff5280b621094eef47c0e3ffdc0778084184`) and wrote two evidence rows: function inventory `add`, `main`, and a decompilation of `main` that calls `add`. The sample file mode was left unchanged and the guest did not execute it. The console investigation page shows “Ghidra 11.4.3”, both function names, and the decompilation. On 2026-11-15 the owner looked at that page and accepted it.
- Follow-ons filed: PE analysis stays on the Windows guest and is not this order. New uploads on the Mac are not yet copied to the guest automatically.
- Residual risks: the database tunnel and the artifact copy are operator steps. If either is down, the guest cannot finish a job. The API still does not launch Ghidra.
- Docs/status updated: `docs/status.md`.
- Status surfaces reconciled: `docs/status.md` lists WO-004 under Complete.
- Summary metadata reviewed: focus, phase, and blocked fields in `docs/status.md`.
- Planning-only change? No
