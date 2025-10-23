import os

from pydantic import Field

from sgr_deep_research.core.base_tool import BaseTool
from sgr_deep_research.core.models import ResearchContext
from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH


class GetSizeTool(BaseTool):
    """Get the size of a file or directory.

    Args:
        file_or_dir_path: The path to the file or directory.
                          If empty string, returns total memory directory size.

    Returns:
        The size of the file or directory in bytes.
    """

    reasoning: str = Field(description="Why do you need get size? (1-2 sentences MAX)", max_length=200)
    file_or_dir_path: str = Field(description="The path to the file or directory.")

    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.file_or_dir_path)
        # Handle empty string by returning total memory size
        if not final_path or final_path == "":
            # Get the current working directory (which should be the memory root)
            cwd = MEMORY_PATH
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(cwd):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        pass
            return str(total_size)

        # Otherwise check the specific path
        if os.path.isfile(final_path):
            return str(os.path.getsize(final_path))
        elif os.path.isdir(final_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(final_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        pass
            return str(total_size)
        else:
            raise FileNotFoundError(f"Path not found: {final_path}")
