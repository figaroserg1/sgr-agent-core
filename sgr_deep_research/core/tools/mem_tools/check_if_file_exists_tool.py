from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field
from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH
import os

from sgr_deep_research.core.models import ResearchContext


class CheckIfFileExistsTool(BaseTool):
    """
    Check if a file exists in the given filepath.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        True if the file exists and is a file, False otherwise.
    """

    reasoning: str = Field(description="Why do you need delete file? (1-2 sentences MAX)", max_length=200)
    file_path: str = Field(description="The path to the path")
    
    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.file_path)
        try:
            return str(os.path.exists(final_path) and os.path.isfile(final_path))
        except (OSError, TypeError, ValueError):
            return "False"

    
