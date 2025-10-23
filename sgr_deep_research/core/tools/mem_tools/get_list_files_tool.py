from sgr_deep_research.core.base_tool import BaseTool
from pydantic import Field
import uuid

import os

from sgr_deep_research.core.tools.mem_tools.settings import MEMORY_PATH

from sgr_deep_research.core.models import ResearchContext


class GetListFilesTool(BaseTool):
    """
    Display all files and directories in the current working directory as a tree structure.
    
    Example output:
    ```
    ./
    ├── user.md
    └── entities/
        ├── 452_willow_creek_dr.md
        └── frank_miller_plumbing.md
    ```

    Returns:
        A string representation of the directory tree.
    """

    reasoning: str = Field(description="Why do you need create file? (1-2 sentences MAX)", max_length=200)
    
    async def __call__(self, context: ResearchContext) -> str:
        try:
            # Always use current working directory
            dir_path = MEMORY_PATH
            
            def build_tree(start_path, prefix="", is_last=True):
                """Recursively build tree structure"""
                entries = []
                try:
                    items = sorted(os.listdir(start_path))
                    # Filter out hidden files and __pycache__
                    items = [item for item in items if not item.startswith('.') and item != '__pycache__']
                except PermissionError:
                    return f"{prefix}[Permission Denied]\n"
                
                if not items:
                    return ""
                
                for i, item in enumerate(items):
                    item_path = os.path.join(start_path, item)
                    is_last_item = i == len(items) - 1
                    
                    # Choose the right prefix characters
                    if is_last_item:
                        current_prefix = prefix + "└── "
                        extension = prefix + "    "
                    else:
                        current_prefix = prefix + "├── "
                        extension = prefix + "│   "
                    
                    if os.path.isdir(item_path):
                        # Check if directory is empty
                        try:
                            dir_contents = [f for f in os.listdir(item_path) 
                                        if not f.startswith('.') and f != '__pycache__']
                            if not dir_contents:
                                entries.append(f"{current_prefix}{item}/ (empty)\n")
                            else:
                                entries.append(f"{current_prefix}{item}/\n")
                                # Recursively add subdirectory contents
                                entries.append(build_tree(item_path, extension, is_last_item))
                        except PermissionError:
                            entries.append(f"{current_prefix}{item}/ [Permission Denied]\n")
                    else:
                        entries.append(f"{current_prefix}{item}\n")
                
                return "".join(entries)
            
            # Start with the root directory
            tree = f"./\n{build_tree(dir_path)}"
            return tree.rstrip()  # Remove trailing newline
            
        except Exception as e:
            return f"Error: {e}"


    
