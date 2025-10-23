from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field

import os

from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH
from sgr_deep_research.core.models import ResearchContext


class DeleteFileTool(BaseTool):
    """
    Delete a file in the memory.

    Args:
        file_path: The path to the file.

    Returns:
        True if the file was deleted successfully, False otherwise.
    """

    reasoning: str = Field(description="Why do you need delete file? (1-2 sentences MAX)", max_length=200)
    file_path: str = Field(description="The path to the file.")
    
    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.dir_path)
        try:
            os.remove(final_path)
            return "True"
        except Exception:
            return "False"

    
