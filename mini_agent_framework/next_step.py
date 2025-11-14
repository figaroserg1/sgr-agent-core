"""Utilities for building dynamic next-step schemas."""
from __future__ import annotations

import operator
from functools import reduce
from typing import Annotated, Literal, Type, TypeVar

from pydantic import BaseModel, Field, create_model

from .tool_registry import BaseTool

T = TypeVar("T", bound=BaseTool)


class DiscriminatedToolMixin(BaseModel):
    """Adds a discriminator field so Pydantic can pick the right tool model."""

    tool_name_discriminator: str = Field(..., description="Tool name discriminator")

    def model_dump(self, *args, **kwargs):  # type: ignore[override]
        exclude = set(kwargs.pop("exclude", set()))
        exclude.add("tool_name_discriminator")
        return super().model_dump(*args, exclude=exclude, **kwargs)


class NextStepDecision(BaseModel):
    """Base structure returned by the planner LLM."""

    thought: str = Field(..., description="Short reasoning before the action")
    function: BaseTool = Field(..., description="The next tool to execute")


class NextStepToolsBuilder:
    """Builder that returns a concrete NextStepDecision for any tool list."""

    @classmethod
    def _create_discriminated_tool(cls, tool_class: Type[T]) -> Type[BaseModel]:
        return create_model(
            f"D_{tool_class.__name__}",
            __base__=(tool_class, DiscriminatedToolMixin),
            tool_name_discriminator=(
                Literal[tool_class.tool_name],
                Field(..., description="Tool name discriminator"),
            ),
        )

    @classmethod
    def _create_tool_union(cls, tools: list[Type[T]]):
        if len(tools) == 1:
            return cls._create_discriminated_tool(tools[0])
        discriminated = [cls._create_discriminated_tool(t) for t in tools]
        return Annotated[reduce(operator.or_, discriminated), Field()]

    @classmethod
    def build_next_step_schema(cls, tools: list[Type[T]]) -> Type[NextStepDecision]:
        return create_model(
            "NextStepDecisionModel",
            __base__=NextStepDecision,
            function=(cls._create_tool_union(tools), Field()),
        )
