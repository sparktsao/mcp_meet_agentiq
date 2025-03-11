"""
Parsing utilities for AI responses.
"""
import json
from typing import Tuple, Dict, Any, Optional

def parse_ai_response(content: str) -> Tuple[Optional[bool], Optional[str], Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    Parses the AI response and extracts relevant fields.

    Args:
        content (str): The raw response from the AI.

    Returns:
        tuple: (need_tool, tool_server, tool_name, tool_args, final_answer)
    """
    try:
        # Try to parse the response as JSON
        response_data = json.loads(content)

        # Extract tool invocation details
        need_tool = response_data.get("tool_call", False)
        tool_server = response_data.get("tool_server", None)
        tool_name = response_data.get("tool", None)
        tool_args = response_data.get("tool_args", {}) if need_tool else None

        rdata = response_data.get("response", "")
        if isinstance(rdata, list):
            rdata = "\n".join([str(x) for x in rdata])
        elif isinstance(rdata, dict):
            rdata = str(rdata)

        # Extract the final response (if no tool call is needed)
        final_answer = rdata.strip()

        return need_tool, tool_server, tool_name, tool_args, final_answer

    except json.JSONDecodeError:
        # If the AI returned invalid JSON, treat it as a direct response
        print("Loading AI JSON response failed!!!")
        print(content)
        return None, None, None, None, content.strip()
