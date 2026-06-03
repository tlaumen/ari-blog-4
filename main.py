"""Local OSS entrypoint for running your workflow in the terminal."""

from ari_core.runtime import run_local_workflow

from workflow import registry


if __name__ == "__main__":
    run_local_workflow(registry)
