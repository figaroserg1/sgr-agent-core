"""Example tools used in the minimal demo."""
from __future__ import annotations

from collections import Counter

from .tool_registry import BaseTool


class GenerateKeywordsTool(BaseTool):
    """Pick the most common meaningful words from the conversation."""

    tool_name = "generate_keywords"
    max_keywords: int = 3

    def __call__(self, context: dict) -> str:  # type: ignore[override]
        user_text = " ".join(message["content"] for message in context.get("messages", []) if message["role"] == "user")
        words = [w.lower().strip(",.?!") for w in user_text.split() if len(w) > 3]
        keywords = [word for word, _ in Counter(words).most_common(self.max_keywords)]
        context.setdefault("keywords", keywords)
        return f"Keywords: {', '.join(keywords)}"


class DraftDescriptionTool(BaseTool):
    """Create a short description from the task and discovered keywords."""

    tool_name = "draft_description"
    tone: str = "neutral"

    def __call__(self, context: dict) -> str:  # type: ignore[override]
        task = context.get("task", "")
        keywords = context.get("keywords", [])
        description = f"{task} (keywords: {', '.join(keywords)})"
        context["description"] = description
        return f"Draft description with {self.tone} tone: {description}"


class FinishTool(BaseTool):
    """Return the aggregated result and stop the loop."""

    tool_name = "finish"
    is_terminal: bool = True

    def __call__(self, context: dict) -> str:  # type: ignore[override]
        description = context.get("description", "No description generated")
        keywords = context.get("keywords", [])
        return f"Final output:\n- Description: {description}\n- Keywords: {', '.join(keywords)}"
