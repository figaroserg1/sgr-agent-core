from sgr_deep_research.core.tools.mem_tools.check_if_dir_exists_tool import CheckIfDirExistsTool
from sgr_deep_research.core.tools.mem_tools.check_if_file_exists_tool import CheckIfFileExistsTool
from sgr_deep_research.core.tools.mem_tools.create_dir_tool import CreateDirTool
from sgr_deep_research.core.tools.mem_tools.create_file_tool import CreateFileTool
from sgr_deep_research.core.tools.mem_tools.delete_file_tool import DeleteFileTool
from sgr_deep_research.core.tools.mem_tools.final_mem_tools import FinalTool
from sgr_deep_research.core.tools.mem_tools.get_list_files_tool import GetListFilesTool
from sgr_deep_research.core.tools.mem_tools.get_size_tool import GetSizeTool
from sgr_deep_research.core.tools.mem_tools.go_to_link_tool import GoToLinkTool
from sgr_deep_research.core.tools.mem_tools.read_file_tool import ReadFileTool
from sgr_deep_research.core.tools.mem_tools.update_file_tool import UpdateFileTool

# Tool lists for backward compatibility
mem_agent_tools = [
    CreateFileTool,
    GetSizeTool,
    ReadFileTool,
    CheckIfFileExistsTool,
    CheckIfDirExistsTool,
    CreateDirTool,
    GetListFilesTool,
    DeleteFileTool,
    UpdateFileTool,
    GoToLinkTool,
    FinalTool,
]
