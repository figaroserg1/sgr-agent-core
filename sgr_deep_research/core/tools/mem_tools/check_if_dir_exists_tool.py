from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field
from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH

import os

from sgr_deep_research.core.models import ResearchContext


class CheckIfDirExistsTool(BaseTool):
    """
    Check if a directory exists in the given filepath.
    
    Args:
        dir_path: The path to the directory.
        
    Returns:
        True if the directory exists and is a directory, False otherwise.
    """

    reasoning: str = Field(description="Why do you need delete file? (1-2 sentences MAX)", max_length=200)
    dir_path: str = Field(description="The path to the directory")
    
    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.dir_path)
        try:
            return str(os.path.exists(final_path) and os.path.isdir(final_path))
        except (OSError, TypeError, ValueError):
            return "False"

    
