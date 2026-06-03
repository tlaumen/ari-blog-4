# Core Concepts

This page defines the minimum mental model for building Ari Core workflows.

## Building blocks

- **DataModel**: typed value object passed between steps.
- **Step**: unit of workflow logic (`execute(ctx)`).
- **Segment**: user-selectable flow made of ordered step classes.
- **SegmentRegistry**: registry of available segments.
- **Table.WORKFLOW**: per-run/session state.
- **Table.PROJECT**: persistent project-level state.

## Execution lifecycle

1. User selects an available segment.
2. Steps run in order.
3. For each step:
   - declared `requires` are loaded into `ctx`
   - `execute(ctx)` runs
   - declared `produces` are persisted from `ctx`
4. User can select another segment or finish.

## Step invariants (must hold)

- Every key declared in `produces` must be written into `ctx` before return.
- `steps=[...]` in a `Segment` must contain **step classes**, not instances.
- Types used across producer/consumer steps must match.

## Availability model

A segment is available only when all its segment-level `requires` are satisfied in workflow state.

## Interaction model

Use primitives inside step execution:
- `prompt(...)`
- `choice(...)`
- `confirm(...)`
- `ui(...)`

They require an active workflow runtime/session.

## Storage rule of thumb

- Default to `Table.WORKFLOW`.
- Use `Table.PROJECT` only when value must survive across runs.
