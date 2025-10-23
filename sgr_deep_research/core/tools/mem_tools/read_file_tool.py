import os

from pydantic import Field

from sgr_deep_research.core.base_tool import BaseTool
from sgr_deep_research.core.models import ResearchContext
from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH


class ReadFileTool(BaseTool):
    """Read a file in the memory.

    Args:
        file_path: The path to the file.

    Returns:
        The content of the file, or an error message if the file cannot be read.
    """

    reasoning: str = Field(description="Why do you need read file? (1-2 sentences MAX)", max_length=200)
    file_path: str = Field(description="The path to the file.")

    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.file_path)
        try:
            # Ensure the file path is properly resolved
            if not os.path.exists(final_path):
                return f"Error: File {final_path} does not exist"

            if not os.path.isfile(final_path):
                return f"Error: {final_path} is not a file"

            with open(final_path, "r") as f:
                return f.read()
        except PermissionError:
            return f"Error: Permission denied accessing {final_path}"
        except Exception as e:
            return f"Error: {e}"
