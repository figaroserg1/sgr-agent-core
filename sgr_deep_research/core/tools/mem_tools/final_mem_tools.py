from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field
from sgr_deep_research.core.models import AgentStatesEnum
from sgr_deep_research.core.models import ResearchContext


class FinalTool(BaseTool):
    """
    Use this tool if you have completed all the necessary steps.
    """

    reasoning: str = Field(description="Why do you need delete file? (1-2 sentences MAX)", max_length=200)
    
    async def __call__(self, context: ResearchContext) -> str:
        context.state = AgentStatesEnum.COMPLETED
        return "The work was completed."

    
