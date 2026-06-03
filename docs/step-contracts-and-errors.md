# Step Contracts and Errors

This page defines strict step execution contracts and how to fix common failures.

## Execution contract

For each step run, Ari Core does:

1. Load each declared `Requirement` into `ctx[requirement.key]`
2. Call `execute(ctx)`
3. Validate every declared `Product(key=...)` exists in `ctx`
4. Persist each product to its declared destination table

If your step violates this contract, execution fails.

## Non-negotiable invariants

- Every declared product key must be written before `execute` returns.
- Step `produces` keys and `ctx[...]` keys must match exactly.
- Consumer `Requirement.model` must match producer output type.
- Segment `steps=[...]` must use step classes, not step instances.

## Common errors and fixes

### Error: declared product missing from ctx

**Symptom**
- `declared product 'x' missing from ctx`

**Cause**
- You declared `Product(key="x", ...)` but never set `ctx["x"]`.

**Fix**
- Write `ctx["x"] = <value>` before returning.

---

### Error: KeyError for required value

**Symptom**
- `KeyError` when reading `ctx["some_key"]`

**Cause**
- Required key not produced earlier, wrong key name, or wrong table boundary.

**Fix**
- Verify producer/consumer key names are identical.
- Verify producer destination (`WORKFLOW` vs `PROJECT`) matches consumer source.

---

### Error: Type mismatch when loading workflow value

**Symptom**
- `expected ModelA, got ModelB`

**Cause**
- Producer wrote a different model/value type than consumer expects.

**Fix**
- Align producer output type with consumer `Requirement.model`.

---

### Error: prompt called outside active session

**Symptom**
- `prompt() called outside of an active session`

**Cause**
- Prompting API used outside workflow runtime execution.

**Fix**
- Only call `prompt/choice/confirm/ui` from step execution in a running workflow.

---

### Error: ui component missing render_html

**Symptom**
- `ui() component must have render_html()`

**Cause**
- Component passed to `ui(...)` does not implement required method.

**Fix**
- Add `render_html(self) -> str` to component.

## Minimal debug checklist

- [ ] Do `produces` keys exactly match written `ctx` keys?
- [ ] Are `Requirement.key` names consistent across steps?
- [ ] Are producer/consumer model types aligned?
- [ ] Is table usage correct (`WORKFLOW` vs `PROJECT`)?
- [ ] Are prompts executed only inside runtime-managed step execution?

## Good vs bad examples

### Bad (missing product write)

```python
class BadStep(Step):
    name = "bad"
    requires = []
    produces = [Product(key="result", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        text = prompt("Enter text")
        # forgot: ctx["result"] = ...
```

### Good (product write present)

```python
class Result(DataModel):
    text: str


class GoodStep(Step):
    name = "good"
    requires = []
    produces = [Product(key="result", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        text = prompt("Enter text")
        ctx["result"] = Result(text=text)
```

## Related docs

- `docs/core-concepts.md`
- `docs/step-authoring.md`
- `docs/api-cheatsheet.md`
