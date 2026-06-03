# Publish to Demo

You can publish your workflow project to the hosted demo environment with the CLI.

## Happy path

From your workflow project directory:

```bash
uv run ari demo-push
```

If your project is not initialized for demo use yet, run:

```bash
uv run ari demo-init
```

Then publish again:

```bash
uv run ari demo-push
```

## Why use it

- Share a real hosted run quickly
- Let stakeholders test in a browser
- Reduce setup friction for evaluation and onboarding
