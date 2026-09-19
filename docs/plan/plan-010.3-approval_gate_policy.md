-- approval_gate_policy

# Skill: State-Gated Reporting Assertions

## Intent Context
Applied by orchestration loops evaluating task lifecycles.

## Core Directives
1. **Compilation Intercept:** Do not fire the summary generator when a task state is set to `Active`, `Pending`, or `Failed Verification`.
2. **Execution Gate:** Trigger compilation exclusively when an explicit confirmation parameter flags a module as `Approved`.
