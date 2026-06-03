# Step Authoring

A step reads required inputs, performs logic, and writes typed outputs.

## Core shape

```python
from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext


class GreetingResult(DataModel):
    name: str


class ExampleStep(Step):
    name = "example"
    requires = []
    produces = [Product(key="greeting", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        name = prompt("What is your name?")
        ctx["greeting"] = GreetingResult(name=name)
```

## Design heuristics

- Keep each step focused on one responsibility.
- Prefer small, composable steps over one large step.
- Make outputs explicit and strongly typed.
- Keep side effects local and predictable.

## Input/output contracts

- `requires` declares what a step needs.
- `produces` declares what a step must write.
- `ctx` is the execution boundary: read required inputs, write declared outputs.

Producer/consumer alignment example:

```python
from ari_core.models import DataModel, Table
from ari_core.workflow.step import Product, Requirement, Step, StepContext


class ParsedName(DataModel):
    first: str
    last: str


class ParseNameStep(Step):
    name = "parse_name"
    requires = []
    produces = [Product(key="parsed_name", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        ctx["parsed_name"] = ParsedName(first="Ada", last="Lovelace")


class UseNameStep(Step):
    name = "use_name"
    requires = [Requirement(key="parsed_name", source=Table.WORKFLOW, model=ParsedName)]
    produces = [Product(key="welcome", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        parsed = ctx["parsed_name"]
        ctx["welcome"] = f"Hello {parsed.first} {parsed.last}"
```

## Prompting patterns

Use interaction primitives only inside step execution:

- `prompt(message)`
- `choice(message, choices)`
- `confirm(message, default=False)`
- `ui(component)`

Example with parsing/validation boundary:

```python
from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext


class Quantity(DataModel):
    count: int


class AskQuantityStep(Step):
    name = "ask_quantity"
    requires = []
    produces = [Product(key="quantity", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        raw = prompt("How many items?")
        count = int(raw)
        ctx["quantity"] = Quantity(count=count)
```

## `ui(component)` contract

- Component must implement `render_html() -> str`.
- Return values via `window.parent.postMessage({value: ...}, '*')`.
- For hosted-safe UI, avoid inline handlers/scripts and CDN scripts.

## Storage decisions in step authoring

- Use `Table.WORKFLOW` for intermediate run values.
- Use `Table.PROJECT` for persistent project-level data.
- Default to `WORKFLOW` unless persistence is explicitly needed.

## Anti-patterns and rewrites

### Anti-pattern: declared product never written

```python
produces = [Product(key="result", dest=Table.WORKFLOW)]

# execute forgets to write ctx["result"]
```

Rewrite:

```python
ctx["result"] = Result(...)
```

### Anti-pattern: inconsistent key naming

Bad:

```python
# producer writes
ctx["parsed"] = ParsedName(...)

# consumer requires
Requirement(key="parsed_name", source=Table.WORKFLOW, model=ParsedName)
```

Rewrite: use one canonical key across both steps.

### Anti-pattern: overly broad step

Bad: one step does input collection, parsing, persistence, and reporting.

Rewrite: split into focused steps (collect -> transform -> output).

## Pre-commit checklist

- [ ] Step has one clear responsibility
- [ ] `requires` and `produces` are complete and minimal
- [ ] Every declared product key is written
- [ ] Output types are explicit and consistent
- [ ] Storage destination is intentional (`WORKFLOW` or `PROJECT`)

## Related docs

- `docs/step-contracts-and-errors.md`
- `docs/core-concepts.md`
- `docs/api-cheatsheet.md`
