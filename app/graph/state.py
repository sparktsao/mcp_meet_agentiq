"""
State definitions for LangGraph.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from tools.mcp_manager import MCPToolManager

class MyState:
    """
    Custom state class for maintaining application state.
    """
    def __init__(
        self,
        user_input: str,
        tool_invocation_needed: bool = False,
        tool_server: str = "",
        tool_name: str = "",
        tool_arguments: Optional[Dict[str, Any]] = None,
        tool_result: str = "",
        final_answer: str = ""
    ):
        self.user_input = user_input
        self.tool_invocation_needed = tool_invocation_needed
        self.tool_server = tool_server
        self.tool_name = tool_name
        self.tool_arguments = tool_arguments or {}
        self.tool_result = tool_result
        self.final_answer = final_answer
        self.chat_history = []
        
        # Tool usage counter dictionary to track how many times each tool has been used
        # Format: {tool_server: {tool_name: count}}
        self.tool_usage_counts: Dict[str, Dict[str, int]] = {}
        
        # Maximum allowed uses per tool (can be customized)
        self.max_tool_uses: int = 1

        # These will be set later
        self.llm = None
        self.tool_manager: Optional[MCPToolManager] = None

@dataclass
class GraphState:
    """
    Dataclass for LangGraph state.
    """
    tool_invocation_needed: bool = False
    tool_server: str = ""
    tool_name: str = ""
    tool_arguments: Dict[str, Any] = None
    tool_result: str = ""
    final_answer: str = ""

    def __post_init__(self):
        if self.tool_arguments is None:
            self.tool_arguments = {}
