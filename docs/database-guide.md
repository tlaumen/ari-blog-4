# Database Guide

Use storage intentionally. Most workflow bugs come from wrong table boundaries.

## Two storage scopes

- `Table.WORKFLOW`: per-run/session state (transient)
- `Table.PROJECT`: project-level state (persistent)

## Decision matrix

Use `Table.WORKFLOW` when:
- value is intermediate
- value is only needed in the current run
- value should reset naturally between runs

Use `Table.PROJECT` when:
- value is shared across multiple runs
- value is configuration/reference data
- value is long-lived project state

## Boundary examples

### Example A: transient parsing result

- user enters free text
- step parses structure
- later step uses parsed structure in same run

Use: `Table.WORKFLOW`

### Example B: reusable user profile

- collect organization/profile metadata once
- reuse in later runs

Use: `Table.PROJECT`

### Example C: generated report draft

- draft produced and reviewed in one interactive session

Use: `Table.WORKFLOW` (unless you explicitly need to reopen drafts later)

## Typical pattern

```python
from ari_core.models import DataModel, Table
from ari_core.workflow.step import Product

class Draft(DataModel):
    text: str

produces = [Product(key="draft", dest=Table.WORKFLOW)]
```

## Refactor guidance: when scope changes

If a value starts as transient but later must persist:

1. change producer destination from `WORKFLOW` to `PROJECT`
2. update consumer requirements source to `PROJECT`
3. keep key/model consistent to reduce migration friction

If a value was persistent but should become transient, do the reverse.

## Anti-patterns

### Anti-pattern: storing everything in PROJECT

Leads to stale/hidden coupling between runs.

Rewrite: default to `WORKFLOW`, promote only when persistence is truly needed.

### Anti-pattern: inconsistent source/destination

Producer writes to `WORKFLOW` while consumer reads from `PROJECT`.

Rewrite: align source/destination on both sides.

## Checklist

- [ ] Is persistence actually required?
- [ ] Do producer destination and consumer source match?
- [ ] Are key/model names stable across steps?
- [ ] Could this safely default to `WORKFLOW`?

## Related docs

- `docs/core-concepts.md`
- `docs/step-authoring.md`
- `docs/segment-guide.md`
