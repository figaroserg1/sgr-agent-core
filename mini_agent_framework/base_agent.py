"""Minimal agent loop demonstrating the dynamic schema."""
from __future__ import annotations

from typing import Iterable, Type

from .llm import RuleBasedPlannerLLM
from .next_step import NextStepToolsBuilder
from .tool_registry import BaseTool


class AgentState(dict):
    """Holds the conversation history and shared context."""

    def append(self, role: str, content: str) -> None:
        self.setdefault("messages", []).append({"role": role, "content": content})

    @property
    def messages(self) -> list[dict]:
        return self.setdefault("messages", [])


class BaseAgent:
    """Coordinates context, schema building, and tool execution."""

    def __init__(self, task: str, llm: RuleBasedPlannerLLM, toolkit: Iterable[Type[BaseTool]]):
        self.task = task
        self.llm = llm
        self.toolkit = list(toolkit)
        self.state = AgentState(task=task, messages=[{"role": "user", "content": task}])

    def _build_schema(self):
        return NextStepToolsBuilder.build_next_step_schema(self.toolkit)

    def _select_next_step(self):
        schema = self._build_schema()
        return self.llm.complete(self.state.messages, schema, tools=self.toolkit)

    def run(self) -> str:
        """Execute tools until one of them signals completion."""

        while True:
            decision = self._select_next_step()
            tool: BaseTool = decision.function
            self.state.append("assistant", decision.thought)
            result = tool(self.state)
            self.state.append("tool", result)
            if getattr(tool, "is_terminal", False):
                return result
