"""Tool definitions for the arXiv MCP server."""

import sys
#sys.path.append('/Users/sparkt/2024_CODE/arxiv-mcp-server/src/')

from arxiv_mcp_server.tools.search import search_tool, handle_search
from arxiv_mcp_server.tools.download import download_tool, handle_download
from arxiv_mcp_server.tools.list_papers import list_tool, handle_list_papers
from arxiv_mcp_server.tools.read_paper import read_tool, handle_read_paper


__all__ = [
    "search_tool",
    "download_tool",
    "read_tool",
    "handle_search",
    "handle_download",
    "handle_read_paper",
    "list_tool",
    "handle_list_papers",
]
