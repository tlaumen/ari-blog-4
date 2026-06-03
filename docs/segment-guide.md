# Segment Guide

A segment is a user-selectable workflow entrypoint made of ordered step classes.

## Core registration

```python
from ari_core.workflow.registry import SegmentRegistry
from ari_core.workflow.segment import Segment

from steps.example_step import ExampleStep

registry = SegmentRegistry()

registry.register(
    Segment(
        name="example",
        description="Run example flow",
        steps=[ExampleStep],
        requires=[],
    )
)
```

## Design patterns

### 1) Single-intent segment

Each segment should represent one user intent (e.g. "collect profile", "generate report").

### 2) Progressive disclosure

Start with segments that collect prerequisite data, then unlock follow-up segments via `requires`.

### 3) Small step chains

Prefer short, comprehensible step chains over long monolithic segments.

## Dependency gating with `requires`

Segment-level `requires` controls when a segment appears.

```python
from ari_core.models import Table
from ari_core.workflow.step import Requirement

Segment(
    name="review_report",
    description="Review generated report",
    steps=[...],
    requires=[
        Requirement(key="report", source=Table.WORKFLOW, model=ReportModel),
    ],
)
```

If `report` is missing, the segment is not available yet.

## Cross-segment flow pattern

- Segment A produces `draft`.
- Segment B requires `draft`, produces `approved_draft`.
- Segment C requires `approved_draft`.

This creates explicit workflow progression without hidden coupling.

## Anti-patterns

### Anti-pattern: one giant segment

A segment with too many unrelated responsibilities is hard to maintain.

Rewrite: split into focused segments and gate with `requires`.

### Anti-pattern: ambiguous keys

Using vague keys (`data`, `result`) across segments causes collisions/confusion.

Rewrite: use explicit keys (`customer_profile`, `report_draft`, `approval_decision`).

### Anti-pattern: implicit dependencies

Consumer steps expecting values that are not declared in segment/step requirements.

Rewrite: declare `Requirement` explicitly.

## Checklist

- [ ] Segment name is unique and intent-revealing
- [ ] Steps are ordered by dependency
- [ ] `requires` accurately represent prerequisites
- [ ] Output keys are explicit and consistent across segments

## Related docs

- `docs/core-concepts.md`
- `docs/step-authoring.md`
- `docs/database-guide.md`
