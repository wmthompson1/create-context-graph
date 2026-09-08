# Demo Output 02 — Schedule Contention Example

## Scenario

User asks: "Are there overlapping schedule slots for WorkCenter Y tomorrow?"

## Evidence path

WorkCenter → hasScheduleSlot → ScheduleSlot

## Output summary

The agent compares planned time intervals for the same work center and reports whether they overlap.

- WorkCenter: `WC-17`
- ScheduleSlot A: `SS-17-01`, 08:00–10:00
- ScheduleSlot B: `SS-17-02`, 09:30–11:30
- ScheduleSlot C: `SS-17-03`, 13:00–15:00

## Example response

"For WorkCenter WC-17, the graph shows overlapping schedule slots tomorrow. ScheduleSlot SS-17-01 runs from 08:00 to 10:00 and ScheduleSlot SS-17-02 runs from 09:30 to 11:30. The intervals overlap from 09:30 to 10:00, which indicates schedule contention for that work center."

## Why this matters

This demonstrates operational reasoning in a second key manufacturing domain:
- capacity planning
- event timing
- evidence-backed schedule conflict detection
- no speculative inference beyond the actual slot overlaps

## PM talking point

"This is not just a calendar view. It is a graph-based capacity check that can explain why a work center is overloaded and which slots are conflicting."
