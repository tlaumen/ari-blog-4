"""
ExampleStep — starter step demonstrating the full Ari workflow pattern.

This step:
1. Prompts the user for their name via the browser UI.
2. Stores the name in the workflow database.
3. Logs the greeting server-side.

Replace or extend this step with your own domain logic.
"""

from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext


class GreetingResult(DataModel):
    """Stored result of the example step."""
    name: str
    greeting: str


class ExampleStep(Step):
    """Prompt the user for their name and store a greeting."""

    name = "example"
    requires = []
    produces = [Product(key="greeting_result", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        # prompt() blocks until the user submits a response via the browser.
        # No async/await required — the framework handles the event loop bridge.
        user_name = prompt("What is your name?")

        greeting = f"Hello, {user_name}!"
        print(greeting)   # visible in server logs

        ctx["greeting_result"] = GreetingResult(
            name=user_name,
            greeting=greeting,
        )
