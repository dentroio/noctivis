# NOCTIVIS architecture (target state)

## Boundaries

- Experience: REST API, web console, CLI.
- Control: identity, RBAC, investigation scope, approval and budget enforcement.
- Reasoning: LangGraph supervisor and specialist agents; all outputs treated as hypotheses until verified.
- Capabilities: versioned plugins with declared tools, permissions, workflows and schemas.
- Tools: Ghidra headless first; later Binary Ninja, angr, debuggers and fuzzers.
- Data: PostgreSQL source of truth; object storage for immutable artifacts; Neo4j for relationships; Qdrant for retrieval.

## Trust model

No model output or binary-embedded string can authorize a tool call. The gateway independently enforces tool policy and per-investigation budgets. Untrusted binaries never execute on the API host. Dynamic execution requires an approved task in a disposable, network-denied VM. Capture hashes, tool versions, provenance and reproducible evidence.

## First vertical slice

Upload a sample ELF -> classify and hash -> persist artifact -> enqueue Ghidra worker -> collect function inventory -> supervisor selects function -> decompile -> store evidence -> generate bounded findings report.

## Not yet implemented

Authentication beyond a single local operator, persistence, worker queues, Ghidra, LangGraph, MCP, and dynamic analysis. The operator console signs in against that local password and does not assign roles or a policy gateway.
