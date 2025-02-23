from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os

# Initialize FastMCP server
mcp = FastMCP("filesearch")

# Constants
SEARCH_DIRECTORY = os.getenv("SEARCH_DIRECTORY", "/")

def debug_log(message: str, filename="debug.log") -> None:
    """Appends debug messages to a log file."""
    log_path = os.path.join(os.getcwd(), filename)  # Save log in the current directory
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


@mcp.tool()
def search_files(partial_name: str) -> list[str]:
    """Search for files with a partial name match in a user-specified folder.

    Args:
        partial_name: Partial filename to search for.

    Returns:
        List of matching file paths.
    """
    matching_files = []

    # Validate search directory
    if not os.path.exists(SEARCH_DIRECTORY):
        return [f"Error: Directory '{SEARCH_DIRECTORY}' does not exist."]

    # Recursively search for files
    for root, _, files in os.walk(SEARCH_DIRECTORY):
        for file in files:
            if partial_name.lower() in file.lower():  # Case-insensitive match
                matching_files.append(os.path.join(root, file))

    return matching_files if matching_files else ["No matching files found."]


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
