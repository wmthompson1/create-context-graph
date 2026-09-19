---
name: approval_gate_policy
description: "Use when: a task lifecycle or orchestration loop needs a report/summary gate before compilation. Enforces no summary generation while status is Active, Pending, or Failed Verification; only compile when an explicit approval flag marks the module as Approved."
---

# Approval Gate Policy

## Intent
Applied by orchestration loops evaluating task lifecycles and reporting readiness.

## Required behavior
1. **Compilation Intercept:** Do not fire the summary generator when a task state is set to `Active`, `Pending`, or `Failed Verification`.
2. **Execution Gate:** Trigger compilation exclusively when an explicit confirmation parameter flags a module as `Approved`.
3. **No-report fallback:** If the task is not explicitly approved, stop before generating a final summary or report.

## Decision rule
- `Active` -> no compilation
- `Pending` -> no compilation
- `Failed Verification` -> no compilation
- `Approved` -> compilation allowed

## Operational expectation
This skill prevents premature reporting. A task can only move to final summary generation after explicit approval, ensuring reporting reflects verified completion rather than in-progress or failed states.
