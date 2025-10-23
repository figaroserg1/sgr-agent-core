from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field

import os

from sgr_deep_research.core.models import ResearchContext


class GoToLinkTool(BaseTool):
    """
    Go to a link in the memory and return the content of the note Y. A link in a note X to a note Y, with the
    path path/to/note/Y.md, is structured like this:
    [[path/to/note/Y]]

    Args:
        link_string: The link to go to.

    Returns:
        The content of the note Y, or an error message if the link cannot be accessed.
    """

    reasoning: str = Field(description="Why do you need delete file? (1-2 sentences MAX)", max_length=200)
    link_string: str = Field(description="The string link to the file.")
    
    async def __call__(self, context: ResearchContext) -> str:
        try:
            # Handle Obsidian-style links: [[path/to/note]] -> path/to/note.md
            if self.link_string.startswith("[[") and self.link_string.endswith("]]"):
                file_path = self.link_string[2:-2]  # Remove [[ and ]]
                if not file_path.endswith('.md'):
                    file_path += '.md'
            else:
                file_path = self.link_string
                
            # Ensure the file path is properly resolved
            if not os.path.exists(file_path):
                return f"Error: File {file_path} not found"
            
            if not os.path.isfile(file_path):
                return f"Error: {file_path} is not a file"
                
            with open(file_path, "r") as f:
                return f.read()
        except PermissionError:
            return f"Error: Permission denied accessing {self.link_string}"
        except Exception as e:
            return f"Error: {e}"

    
