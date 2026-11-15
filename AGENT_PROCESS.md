# Agent Process For Work Orders

NOCTIVIS uses the [Work Order Protocol](https://github.com/dentroio/work-order-protocol) at adoption level 2 (agent-assisted). This file is the process every human and coding agent follows.

Work Orders live in `docs/work_orders/`. Project status lives in `docs/status.md`. Product direction lives in `docs/ROADMAP.md` and is not a second backlog.

## When Asked To Draft A Work Order

Drafting is not implementation authorization.

1. Read this file, `templates/WO-template.md`, `docs/status.md`, and any related Work Orders.
2. Inspect enough code, tests, and documentation to ground the draft in evidence.
3. Separate verified facts from assumptions and recommendations.
4. Mark open decisions that change behavior, scope, risk, or acceptance.
5. Recommend a risk tier. Do not silently lower it.
6. Leave the Work Order in `Draft` until a human accepts it.
7. Do not edit product code, create an implementation branch, or claim the Work Order unless the user separately authorizes implementation.

## Rules

1. Read the assigned Work Order before editing files.
2. Confirm dependencies and risk tier.
3. Stay inside the Work Order scope.
4. Do not expand adjacent work. File a follow-on.
5. Preserve anything listed under "Do NOT Change."
6. Run the validation plan and the quality gate.
7. Ask for human verification when the Work Order requires it.
8. Update `docs/status.md` and the Work Order closeout together.
9. Record verification evidence and follow-ons before closeout.

## Risk Tiers

| Tier | Meaning | Approval |
| --- | --- | --- |
| P0 | Auth, secrets, sample execution, data loss, destructive actions | Human approval required before implementation |
| P1 | API contracts, persistence, core investigation behavior | Human approval required before implementation |
| P2 | Console behavior, ordinary product fixes | Human verification after implementation |
| P3 | Docs and status only | Lightweight review |

If one change spans two tiers, split it.

## Project Invariants

- The console signs in as one local operator whose password comes from the environment. Do not accept an empty or universal password.
- Uploaded samples are stored by hash. Do not execute them on the API host. Remove the temporary upload file after the bytes are in the artifact store.
- `dynamic_execution` stays denied until a later Work Order defines an isolated sandbox.
- Development servers bind to loopback. Do not expose the API or console on a network interface.
- Do not store production credentials in source or fixtures.

## Quality Gate

```bash
pytest -q
cd apps/web && npm run typecheck && npm run build
```

Run the parts that match the files you changed. A console change runs both. A docs-only change does not need the gate, and the Work Order says so.

## Implementation Checklist

```text
Read WO
  -> inspect current state
  -> implement only the scoped change
  -> run the quality gate
  -> manual verification when required
  -> update docs/status.md and the WO closeout
```

## Never Do

- Do not treat vague acceptance criteria as permission to guess.
- Do not silently skip tests.
- Do not mix unrelated cleanup into the Work Order.
- Do not downgrade a risk tier.
- Do not claim completion without verification evidence.
- Do not let a planning-only Work Order count as implementation.
