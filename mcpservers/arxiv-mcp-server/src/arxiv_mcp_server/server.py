"""
Arxiv MCP Server
===============

This module implements an MCP server for interacting with arXiv.
"""
import sys
sys.path.append('/Users/sparkt/2024_CODE/AwesomeMCPChat/mcpservers/arxiv-mcp-server/src')

import logging
import mcp.types as types
from typing import Dict, Any, List
from arxiv_mcp_server.config import Settings
from arxiv_mcp_server.tools import handle_search, handle_download, handle_list_papers, handle_read_paper
from arxiv_mcp_server.tools import search_tool, download_tool, list_tool, read_tool
from arxiv_mcp_server.prompts.handlers import list_prompts as handler_list_prompts
from arxiv_mcp_server.prompts.handlers import get_prompt as handler_get_prompt

settings = Settings()
logger = logging.getLogger("arxiv-mcp-server")
logger.setLevel(logging.INFO)

from mcp.server.fastmcp import FastMCP
# Initialize FastMCP server
mcp = FastMCP("arxiv")

@mcp.tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handles various research-related functionalities for querying and retrieving academic papers from arXiv.

    Parameters:
    - name (str): The name of the tool function to be executed. Supported values:
    - "search_papers": Searches for papers on arXiv based on provided criteria.
    - "download_paper": Downloads a specific paper given its identifier.
    - "list_papers": Retrieves a list of available papers based on user preferences.
    - "read_paper": Reads and returns the content of a specified paper.

    - arguments (Dict[str, Any]): A dictionary containing parameters required for the selected tool function. 
    Expected keys depend on the chosen tool:
    - For "search_papers": May include 'query' (search term), 'max_results' (number of results), and 'sort_by' (sorting criteria like relevance or date).
    - For "download_paper": Requires 'paper_id' (arXiv identifier).
    - For "list_papers": Could include filters like 'category' or 'author'.
    - For "read_paper": Requires 'paper_id' to fetch the content.

    Returns:
    - List[types.TextContent]: A list containing either:
    - The requested information (e.g., search results, paper metadata, or content).
    - An error message if the tool name is invalid or an exception occurs.

    Example Usage:
        await call_tool("search_papers", {"query": "deep learning", "max_results": 5})
    """

    logger.debug(f"Calling tool {name} with arguments {arguments}")
    try:
        if name == "search_papers":
            return await handle_search(arguments)
        elif name == "download_paper":
            return await handle_download(arguments)
        elif name == "list_papers":
            return await handle_list_papers(arguments)
        elif name == "read_paper":
            return await handle_read_paper(arguments)
        else:
            return [types.TextContent(type="text", text=f"Error: Unknown tool {name}")]
    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


if __name__ == "__main__":
    # Initialize and run the FastMCP server
    mcp.run(transport="stdio")

    