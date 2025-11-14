"""Very small LLM abstraction used in the demo agent."""
from __future__ import annotations

from typing import Callable, Iterable, Type

from .next_step import NextStepDecision
from .tool_registry import BaseTool

PlannerCallable = Callable[[list[dict], Iterable[Type[BaseTool]]], dict]


class RuleBasedPlannerLLM:
    """Mock LLM that emits structured responses using a simple planner callback."""

    def __init__(self, planner: PlannerCallable):
        self._planner = planner

    def complete(
        self,
        messages: list[dict],
        response_model: type[NextStepDecision],
        *,
        tools: Iterable[Type[BaseTool]],
    ) -> NextStepDecision:
        payload = self._planner(messages, tools)
        if "function" not in payload:
            raise ValueError("Planner must return a dict with a 'function' key")
        return response_model.model_validate(payload)


class DeterministicLLM(RuleBasedPlannerLLM):
    """Convenience wrapper that chooses tools sequentially."""

    def __init__(self, plan: list[str]):
        def planner(messages: list[dict], tools: Iterable[Type[BaseTool]]) -> dict:
            tool_map = {tool.tool_name: tool for tool in tools}
            step_index = sum(1 for m in messages if m.get("role") == "assistant")
            tool_name = plan[min(step_index, len(plan) - 1)]
            tool_cls = tool_map[tool_name]
            return {
                "thought": f"Using {tool_cls.tool_name} to progress towards the goal.",
                "function": {"tool_name_discriminator": tool_cls.tool_name},
            }

        super().__init__(planner)
