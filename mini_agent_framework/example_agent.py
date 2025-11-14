"""Runnable example showing how to wire the mini framework together."""
from __future__ import annotations

from .base_agent import BaseAgent
from .llm import DeterministicLLM
from .tools import DraftDescriptionTool, FinishTool, GenerateKeywordsTool


def run_demo(task: str) -> str:
    llm = DeterministicLLM(
        plan=[GenerateKeywordsTool.tool_name, DraftDescriptionTool.tool_name, FinishTool.tool_name]
    )
    agent = BaseAgent(task=task, llm=llm, toolkit=[GenerateKeywordsTool, DraftDescriptionTool, FinishTool])
    return agent.run()


if __name__ == "__main__":
    print(run_demo("Create an engaging product listing for organic honey"))
