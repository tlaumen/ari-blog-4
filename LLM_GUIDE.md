# LLM Guide: Implementing Custom Ari Core Workflows

This guide is for LLMs generating code inside a scaffolded Ari project (`uv run ari new`).

## 1) Mental model

Ari Core workflows are built from:
- **Data models** (`DataModel`) for typed values
- **Steps** (`Step`) that read/write a context (`ctx`)
- **Segments** (`Segment`) that group ordered steps
- **Registry** (`SegmentRegistry`) that exposes available segments

Runtime executes steps, persists declared outputs, and repeats segment selection until user chooses `Done`.

## 2) Required code artifacts

For a new workflow feature, generate:
1. One or more `DataModel` classes
2. One or more `Step` subclasses
3. Segment registration in `workflow.py`

Canonical shape:

```python
from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext


class ExampleResult(DataModel):
    value: str


class ExampleStep(Step):
    name = "example"
    requires = []
    produces = [Product(key="example_result", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        value = prompt("Enter value")
        ctx["example_result"] = ExampleResult(value=value)
```

## 3) Step contract rules (critical)

- Every declared `Requirement` must be read from `ctx` using its key.
- Every declared `Product(key=...)` **must** be written to `ctx[key]` before `execute` returns.
- Step outputs should be typed (prefer `DataModel` values).
- Segment `steps` must contain **step classes**, not instances.

## 4) Storage decisions

- Use `Table.WORKFLOW` for per-run/intermediate values.
- Use `Table.PROJECT` for persistent/shared project data.
- Default to `WORKFLOW` unless persistence across runs is required.

## 5) Interaction primitives contract

Use:
- `prompt(message)` -> text input
- `choice(message, choices)` -> one option
- `confirm(message, default=False)` -> bool
- `ui(component)` -> custom UI value

For `ui(component)`:
- component must implement `render_html()`
- hosted-safe components should avoid inline handlers/scripts and CDN JS
- return values through `window.parent.postMessage({value: ...}, '*')`

## 6) Pre-return checklist (LLM self-check)

Before returning code, verify:
- [ ] Step names are unique and descriptive
- [ ] `requires`/`produces` keys match actual `ctx[...]` usage
- [ ] All declared products are written
- [ ] Segment registration includes new step classes
- [ ] Types are consistent between produced and required models
- [ ] `Table.PROJECT` is only used when persistence is intentional

## 7) Quick error triage

- **"declared product ... missing from ctx"** -> step forgot `ctx[product_key] = value`
- **KeyError on workflow/project value** -> requirement key not produced yet (or wrong table)
- **TypeError on model mismatch** -> produced value type differs from required model
- **"ui() component must have render_html()"** -> component missing required method
- **"prompt() called outside of an active session"** -> prompts executed outside workflow runtime

## 8) References in this generated project

- Framework index: `docs/index.md`
- Getting started: `docs/getting-started.md`
- Step patterns: `docs/step-authoring.md`
- Segment composition: `docs/segment-guide.md`
- Data/storage usage: `docs/database-guide.md`
- Demo publishing path: `docs/publish-to-demo.md`
