# Engineering work orders

## WO-001 Persistent state
PostgreSQL migrations for binary, investigation, task, evidence, finding, audit, approval. Replace in-memory dictionaries. Acceptance: restart retains investigations; migration tests pass.

## WO-002 Identity and policy
OIDC authentication, RBAC, scoped investigation permissions, default-deny tool gateway. Acceptance: unauthorized requests denied; audit events emitted.

## WO-003 Artifact storage
Content-addressed immutable binaries in MinIO; size/type controls and retention. Acceptance: hash verification and safe retrieval; no execution.

## WO-004 Ghidra worker
Isolated headless worker for ELF static analysis. Acceptance: function inventory and decompilation linked to binary SHA and tool version.

## WO-005 Agent orchestration
LangGraph supervisor, budgets, checkpointing, deterministic task queue, evidence citations. Acceptance: repeatable bounded investigation of sample binary.

## WO-006 Findings and reporting
Structured hypotheses, provenance, review states, Markdown/JSON report. Acceptance: every claim links to stored evidence.

## WO-007 Dynamic sandbox (later)
Hypervisor VM isolation, network denial, explicit approvals, resource limits, teardown. Acceptance: adversarial isolation tests pass.
