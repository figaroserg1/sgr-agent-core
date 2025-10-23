from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field
import os

from sgr_deep_research.core.models import ResearchContext
from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH


class CreateDirTool(BaseTool):
    """
    Create a new directory in the memory.

    Args:
        dir_path: The path to the directory.

    Returns:
        True if the directory was created successfully, False otherwise.
    """
    reasoning: str = Field(description="Why do you need create directory? (1-2 sentences MAX)", max_length=200)
    dir_path: str = Field(description="The path to the directory.")
    
    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.dir_path)
        try:
            os.makedirs(final_path, exist_ok=True)
            return "True"
        except Exception:
            return "False"



    
