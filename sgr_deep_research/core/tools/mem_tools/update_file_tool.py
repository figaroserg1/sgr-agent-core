from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field
import os

from sgr_deep_research.core.models import ResearchContext
from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH

class UpdateFileTool(BaseTool):
    """
    Simple find-and-replace update method for files.

    This is an easier alternative to write_to_file() that doesn't require
    creating git-style diffs. It performs a simple string replacement.

    Parameters
    ----------
    file_path : str
        Path to the file to update.
    old_content : str
        The exact text to find and replace in the file.
    new_content : str
        The text to replace old_content with.

    Returns
    -------
    Union[bool, str]
        True if successful, error message string if failed.

    Examples
    --------
    # Add a new row to a table
    old = "| TKT-1056  | 2024-09-25 | Late Delivery   | Resolved |"
    new = "| TKT-1056  | 2024-09-25 | Late Delivery   | Resolved |\\n| TKT-1057  | 2024-11-11 | Damaged Item    | Open     |"
    result = update_file("user.md", old, new)
    """
    reasoning: str = Field(description="Why do you need create directory? (1-2 sentences MAX)", max_length=200)
    file_path: str = Field(description="The path to the file.")
    old_content: str = Field(description="The exact text to find and replace in the file.")
    new_content: str = Field(description="The text to replace old_content with.")

    async def __call__(self, context: ResearchContext) -> str:
        final_path = os.path.join(MEMORY_PATH, self.file_path)
        try:
            # Read the current file content
            if not os.path.exists(final_path):
                return f"Error: File '{final_path}' does not exist"

            if not os.path.isfile(final_path):
                return f"Error: '{final_path}' is not a file"

            with open(final_path, "r") as f:
                current_content = f.read()

            # Check if old_content exists in the file
            if self.old_content not in current_content:
                # Provide helpful context about what wasn't found
                preview_length = 50
                preview = self.old_content[:preview_length] + "..." if len(self.old_content) > preview_length else self.old_content
                return f"Error: Could not find the specified content in the file. Looking for: '{preview}'"

            # Count occurrences to warn about multiple matches
            occurrences = current_content.count(self.old_content)
            if occurrences > 1:
                # Still proceed but warn the user
                print(f"Warning: Found {occurrences} occurrences of the content. Replacing only the first one.")

            # Perform the replacement (only first occurrence)
            updated_content = current_content.replace(self.old_content, self.new_content, 1)

            # Check if replacement actually changed anything
            if updated_content == current_content:
                return "Error: No changes were made to the file"

            # Write the updated content back
            with open(final_path, "w") as f:
                f.write(updated_content)

            return "True"

        except PermissionError:
            return f"Error: Permission denied writing to '{final_path}'"
        except Exception as e:
            return f"Error: Unexpected error - {str(e)}"


    
