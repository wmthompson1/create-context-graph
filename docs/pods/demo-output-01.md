# Demo Output 01 — Manufacturing Work-Order Evidence Walkthrough

## Scenario

User asks: "For WorkOrder X, what parts are required and through which BOM?"

## Evidence path

WorkOrder → BillOfMaterials → MaterialRequirement → Part

## Output summary

The agent answers from explicit graph relationships rather than free-form inference.

- WorkOrder: `WO-2048`
- BillOfMaterials: `BOM-2048-A`
- MaterialRequirement: `MR-2048-01`, `MR-2048-02`
- Parts: `P-1001`, `P-1002`, `P-1003`

## Example response

"For WorkOrder WO-2048, the required parts are sourced through BOM-2048-A. The graph shows three material requirements: MR-2048-01, MR-2048-02, and MR-2048-03. These map to parts P-1001, P-1002, and P-1003. The evidence chain is WorkOrder → BillOfMaterials → MaterialRequirement → Part, with each relationship explicitly recorded in the graph."

## Why this matters

This demonstrates the product value directly:
- the answer is explainable
- the evidence chain is visible
- the result is grounded in the ontology, not guessed from names or text similarity
- the reasoning remains read-only and bounded

## PM talking point

"This is the moment when the system stops behaving like a chatbot and starts behaving like an operational reasoning assistant grounded in manufacturing evidence."
