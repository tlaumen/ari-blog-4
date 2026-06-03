# UI Components

Use `ui(component)` when terminal prompts are not enough and you need custom HTML interaction.

## Contract

A component passed to `ui(...)` must implement:

```python
def render_html(self) -> str: ...
```

The returned HTML is shown to the user. To return a value, post a message containing a `value` field.

## Return payload convention

Use:

```javascript
window.parent.postMessage({ value: YOUR_VALUE, summary: "Human summary" }, "*")
```

- `value` is returned to your step.
- `summary` is optional metadata for history/rendering contexts.

## Minimal example

```python
from ari_core.prompting import ui

class ApproveComponent:
    def render_html(self) -> str:
        return """
        <button id='ok'>Approve</button>
        <script>
          document.getElementById('ok').addEventListener('click', function () {
            window.parent.postMessage({ value: true, summary: 'Approved' }, '*');
          });
        </script>
        """

ack = ui(ApproveComponent())
```

## CSP-safe guidance for hosted runtimes

For production-facing components:
- avoid inline event handlers (e.g. `onclick="..."`)
- avoid inline scripts when possible
- avoid CDN-hosted scripts
- prefer same-origin static assets

If you use markdown/document review UIs, prefer built-in `DocumentViewer` for a CSP-compatible path.

## Good vs bad

### Bad

```html
<button onclick="window.parent.postMessage({value: 1}, '*')">Submit</button>
<script src="https://cdn.example.com/lib.js"></script>
```

### Better

```html
<button id="submit">Submit</button>
<script>
  document.getElementById('submit').addEventListener('click', function () {
    window.parent.postMessage({ value: 1 }, '*');
  });
</script>
```

## Common failure

- `ui() component must have render_html()`
  - Cause: object passed to `ui(...)` has no `render_html()`
  - Fix: implement `render_html(self) -> str`

## Related docs

- `docs/step-authoring.md`
- `docs/step-contracts-and-errors.md`
