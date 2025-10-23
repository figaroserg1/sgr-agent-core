import traceback
from typing import Type

from sgr_deep_research.core.agents.sgr_agent import SGRResearchAgent
from sgr_deep_research.core.models import AgentStatesEnum
from sgr_deep_research.core.prompts import PromptLoader
from sgr_deep_research.core.tools import (
    BaseTool,
    NextStepToolsBuilder,
    NextStepToolStub,
    WebSearchTool,
)
from sgr_deep_research.core.tools.mem_tools import mem_agent_tools


class SGRMemAgent(SGRResearchAgent):
    """SGR Tool Calling Research Agent variation for benchmark with automatic
    tool selection."""

    name: str = "sgr_mem_agent"

    def __init__(
        self,
        task: str,
        toolkit: list[Type[BaseTool]] | None = None,
        max_clarifications: int = 3,
        max_searches: int = 4,
        max_iterations: int = 10,
    ):
        super().__init__(task, toolkit, max_clarifications, max_searches, max_iterations)

        self.toolkit = [
            *mem_agent_tools,
            # *research_agent_tools,
            # FinalAnswerTool
        ]

        # report doesn't have to for mem agent
        # self.toolkit.remove(CreateReportTool)

    async def _prepare_tools(self) -> Type[NextStepToolStub]:
        """Prepare tool classes with current context limits."""
        tools = set(self.toolkit)
        # if self._context.iteration >= self.max_iterations:
        # tools = {
        #     FinalAnswerTool,
        # }
        if self._context.searches_used >= self.max_searches:
            tools -= {
                WebSearchTool,
            }
        return NextStepToolsBuilder.build_NextStepTools(list(tools))

    async def _prepare_context(self) -> list[dict]:
        """Prepare conversation context with system prompt."""
        return [
            {"role": "system", "content": PromptLoader.get_system_prompt(self.toolkit)},
            {"role": "system", "content": PromptLoader.get_mem_agent_template()},
            *self.conversation,
        ]

    async def execute(
        self,
    ):
        self.logger.info(f"🚀 Starting for task: '{self.task}'")
        self.conversation.extend(
            [
                {
                    "role": "user",
                    "content": PromptLoader.get_initial_user_request(self.task),
                }
            ]
        )
        try:
            while self._context.state not in AgentStatesEnum.FINISH_STATES.value:
                self._context.iteration += 1
                self.logger.info(f"Step {self._context.iteration} started")

                reasoning = await self._reasoning_phase()
                self._context.current_step_reasoning = reasoning
                action_tool = await self._select_action_phase(reasoning)
                await self._action_phase(action_tool)

        except Exception as e:
            self.logger.error(f"❌ Agent execution error: {str(e)}")
            self._context.state = AgentStatesEnum.FAILED
            traceback.print_exc()
        finally:
            if self.streaming_generator is not None:
                self.streaming_generator.finish()
            self._save_agent_log()


if __name__ == "__main__":
    import asyncio

    async def main():
        agent = SGRMemAgent(
            task="Меня зовут Максим. У меня появилась Жена. Ей 18 лет, ее зовут Алина. ",
            max_iterations=10,
            max_clarifications=2,
            max_searches=3,
        )
        await agent.execute()

    asyncio.run(main())
