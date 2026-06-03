# Ari Workflow Project

This is a starter project for building workflows with `ari-core`.

## Quick Start

### 1. Run the local workflow

```bash
python main.py
```

This starts a local terminal flow:
- segment selection via prompt_toolkit
- `prompt()/choice()/confirm()` in terminal
- `ui(...)` opens local browser renderer

## Project Structure

```
.
├── main.py                    # Local runtime entrypoint
├── workflow.py                # Segment definitions
├── steps/
│   ├── __init__.py
│   └── example_step.py        # Example step
├── .env.example               # Environment variables template
├── LLM_GUIDE.md               # Quick AI-assisted workflow authoring guide
├── docs/                      # Framework docs copied from ari_core
│   ├── index.md
│   └── ...
└── README.md                  # This file
```

## Building a Workflow

### Add a new step

Create a file in `steps/`:

```python
from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext


class MyResult(DataModel):
    field1: str
    field2: int


class MyStep(Step):
    name = "my_step"
    requires = []
    produces = [Product(key="my_result", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        value = prompt("Enter a value:")
        ctx["my_result"] = MyResult(field1=value, field2=42)
```

### Register the step in a segment

Edit `workflow.py`:

```python
from steps.my_step import MyStep

registry.register(Segment(
    name="my_workflow",
    description="My custom workflow",
    steps=[MyStep],
    requires=[],
))
```

## Environment Variables

Copy `.env.example` to `.env` and fill in API keys if needed by your steps.

```bash
cp .env.example .env
```

## Need help?

See `docs/issues.md` for:
- bug reports and feature requests (GitHub Issues)
- direct email questions
