# API Cheatsheet

Quick lookup for common Ari Core authoring APIs.

## Models

```python
from ari_core.models import DataModel, Table, project_table
```

- `DataModel`: base class for typed payloads.
- `Table.WORKFLOW`: transient run state.
- `Table.PROJECT`: persistent project state.
- `@project_table`: register a `DataModel` for typed project table usage.

## Step authoring

```python
from ari_core.workflow.step import Requirement, Product, Step, StepContext
```

- `Requirement(key, source, model)`
- `Product(key, dest)`
- `class MyStep(Step): ...`
- `execute(self, ctx: StepContext) -> None`

## Segments

```python
from ari_core.workflow.segment import Segment
from ari_core.workflow.registry import SegmentRegistry
```

- `Segment(name, description, steps=[...], requires=[...])`
- `registry = SegmentRegistry(); registry.register(segment)`

## Prompting

```python
from ari_core.prompting import prompt, choice, confirm, ui
```

- `prompt(message) -> Any`
- `choice(message, choices) -> str`
- `confirm(message, default=False) -> bool`
- `ui(component) -> Any` (`component.render_html()` required)

## Local run

```python
from ari_core.runtime import run_local_workflow
from workflow import registry

run_local_workflow(registry)
```

## Typical step skeleton

```python
from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext

class Result(DataModel):
    text: str

class MyStep(Step):
    name = "my_step"
    requires = []
    produces = [Product(key="result", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        text = prompt("Enter text")
        ctx["result"] = Result(text=text)
```
