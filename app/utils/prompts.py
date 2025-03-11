"""
Prompt generation utilities.
"""
from typing import Dict, Any
from tools.mcp_manager import MCPToolManager

def generate_system_prompt(tool_manager: MCPToolManager) -> str:
    """
    Generates a system prompt that includes available tools categorized by server, including input schemas.

    Args:
        tool_manager (MCPToolManager): The tool manager instance with available tools.

    Returns:
        str: The formatted system prompt.
    """
    tool_section = []

    # Organize tools by server
    for tool_name, tool_info in tool_manager.tools.items():
        tool_section.append(tool_name)  # Append tool name as a string

        # Convert tool_info (a dict) into a readable string
        tool_section.append(f"  {tool_info}")  # Indented description for readability
        
    formatted_tool_section = "\n".join(tool_section)
    
    # Read the prompt template from file
    try:
        with open("./prompts/prompt_p.txt", "r") as f:
            PROMPT = f.read()
    except FileNotFoundError:
        # Fallback prompt if file not found
        PROMPT = """
        You are an AI assistant with access to the following tools:
        
        {formatted_tool_section}
        
        When you need to use a tool, respond with a JSON object in the following format:
        {{
            "tool_call": true,
            "tool_server": "server_name",
            "tool": "tool_name",
            "tool_args": {{
                "arg1": "value1",
                "arg2": "value2"
            }},
            "response": "Your explanation of what you're doing"
        }}
        
        If you don't need to use a tool, respond with:
        {{
            "tool_call": false,
            "response": "Your response to the user"
        }}
        """
    
    return PROMPT.format(formatted_tool_section=formatted_tool_section)
