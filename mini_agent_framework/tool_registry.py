"""Simple registry keeping track of tool classes."""
from __future__ import annotations

from typing import ClassVar, Dict, Iterable, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound="BaseTool")


class ToolRegistry:
    """Central place where every tool class registers itself."""

    _tools: Dict[str, Type[T]] = {}

    @classmethod
    def register(cls, tool_cls: Type[T], *, name: str | None = None) -> None:
        tool_name = name or getattr(tool_cls, "tool_name", tool_cls.__name__)
        cls._tools[tool_name] = tool_cls

    @classmethod
    def get(cls, name: str) -> Type[T]:
        return cls._tools[name]

    @classmethod
    def all(cls) -> Iterable[Type[T]]:
        return cls._tools.values()


class ToolRegistryMixin:
    """Automatically register subclasses for discovery."""

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore[override]
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in {"BaseTool"}:
            ToolRegistry.register(cls, name=getattr(cls, "tool_name", None))


class BaseTool(BaseModel, ToolRegistryMixin):
    """Base class for every tool in the mini framework."""

    tool_name: ClassVar[str] = ""
    description: ClassVar[str] = ""

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore[override]
        cls.tool_name = cls.tool_name or cls.__name__.lower()
        cls.description = cls.description or (cls.__doc__ or "")
        super().__init_subclass__(**kwargs)

    def __call__(self, context: dict) -> str:
        raise NotImplementedError
