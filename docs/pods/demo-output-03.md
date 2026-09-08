# Demo Output 03 — Supplier Coverage Example

## Scenario

User asks: "Do we have enough supplier coverage for the required parts in WorkOrder X?"

## Evidence path

SupplyCommitment → covers → Part
Supplier → supplies → Part

## Output summary

The agent joins supplier commitments to required parts and evaluates whether coverage exists for the work order’s material requirements.

- WorkOrder: `WO-2048`
- Required Part: `P-1001`, `P-1002`, `P-1003`
- Supplier A: `SUP-01` covers `P-1001`, `P-1002`
- Supplier B: `SUP-02` covers `P-1003`
- SupplyCommitment: `SC-2048-01`, `SC-2048-02`

## Example response

"For WorkOrder WO-2048, the graph shows supplier coverage for all required parts. SupplyCommitment SC-2048-01 covers P-1001 and P-1002 through Supplier SUP-01, and SupplyCommitment SC-2048-02 covers P-1003 through Supplier SUP-02. The evidence is explicit in the graph, and there is no inferred coverage beyond the recorded commitments."

## Why this matters

This demonstrates the strategic manufacturing view:
- supply assurance
- risk visibility
- explicit coverage mapping
- explainable sourcing logic grounded in graph relationships

## PM talking point

"This lets the agent answer whether material demand is covered by one or more suppliers using direct graph evidence, not by vague assumptions or text similarity."
