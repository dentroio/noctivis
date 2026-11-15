# WO-010 — Agent catalog

**Status:** Draft
**Priority:** P2
**Effort:** M
**Owner:** unassigned
**Services / Areas:** apps/web, apps/api

## Problem

WO-005 will add supervisor runs, and the owner wants those agents visible the way the Clarion agent screens are visible: a list with health, then a detail page of the tools and capabilities that agent is allowed to use. Noctivis has a capability registry (`packages/noctivis/registry.py`) and no agent records. Building the list before any agent exists would show an empty or invented catalog.

## Decision Context

- Chosen approach: not chosen. This Work Order is not ready to implement.
- Recommended approach: agents are defined by the system, not created in the form. The Connect section gains an Agents item. The list and detail are read-only. Each agent shows its version, health, purpose, tools, and capabilities. The detail states whether the default model from WO-009 was checked.
- Alternatives rejected: a form that lets the operator invent an agent. Copying Clarion's agent names or tool lists into Noctivis.
- Assumptions: WO-005 is the source of the agent definitions. Until those definitions exist, this page is not implemented.
- Open decisions: what "healthy" means for an agent that has not run, and whether a stopped budget counts as a health failure.

## What To Build / Fix

Under Connect, an Agents page:

- A list of system-defined agents. Each row has the name, a one-line purpose, health, and counts of tools and capabilities.
- A detail page with those tools and capabilities as labels, the version, and the model-connection status.
- An empty state when no agent is registered. No sample agents.

The page does not start a run and does not change tool policy.

## Expected Change Surface

- Expected: read API for agents, Agents list and detail routes in `apps/web`.
- Tests: empty catalog, one fixture agent renders its tools, the page does not expose a create action.
- Docs/status: `docs/status.md`, this Work Order.

## Out Of Scope

- Defining the supervisor or calling tools (WO-005).
- Choosing the model (WO-009).
- Editing an agent's tools in the console.

## Do NOT Change

- Model text never authorizes a tool call.
- Agents are not created from the console.
- Samples are not executed.

## Acceptance Criteria

1. The Agents page lists only agents the system registered, and the detail lists the tools and capabilities for that agent.
2. An operator cannot create, rename, or grant tools from this page.
3. Quality gate passes.

## Validation Plan

- Automated: `pytest -q` and `cd apps/web && npm run typecheck && npm run build`.
- Manual: open Agents, open one agent, and confirm the tools match the registry for that agent.
- Evidence to include: the fixture agent name and its tool list.

## Execution

- **Branch:** `wo/010-agent-catalog`
- **Risk tier:** P2
- **Pre-PR / pre-merge gate:** `pytest -q` and `cd apps/web && npm run typecheck && npm run build`
- **Depends on:** WO-005 for real agents, WO-009 for the Connect section and the default model status
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
