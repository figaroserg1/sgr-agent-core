# Mini Agent Framework

This folder extracts the **dynamic next-step schema** idea from the main project and
shrinks it into a training-friendly example.  The goal is to show how tool classes can be
registered automatically, stitched into a discriminated union, and used by an agent loop
without depending on the deep-research specific features from the main code base.

## Highlights

- `tool_registry.py` – implements a minimal `BaseTool` class with self-registration.
- `next_step.py` – builds a `NextStepDecision` model whose `function` field is a dynamic
  union of the currently available tools.  This mirrors the dynamic schema from the
  production agent.
- `base_agent.py` – contains a tiny agent loop that asks an LLM for the next step, executes
  the selected tool, and keeps the shared context up to date.
- `llm.py` – provides a mock `RuleBasedPlannerLLM` so the example is runnable without
  network access.
- `tools.py` & `example_agent.py` – show how to define custom tools and execute an agent
  end to end.

## Running the demo

```bash
python -m mini_agent_framework.example_agent
```

The script runs an agent over three tools:

1. `GenerateKeywordsTool` collects keywords from the user's request.
2. `DraftDescriptionTool` turns those keywords into a product description.
3. `FinishTool` returns the aggregated result and stops the loop.

Because the next-step schema is created from the tool list every iteration, you can add or
remove tools and the `DetermininisticLLM` (or any real LLM) will immediately see the updated
schema without any additional plumbing.
