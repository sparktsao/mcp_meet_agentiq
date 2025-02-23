from typing import Any
import os
import heapq
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("recentfiles")

# Constants
SEARCH_DIRECTORY = os.getenv("SEARCH_DIRECTORY", "/")

TOP_N = 20  # Number of top recent files to retrieve


def debug_log(message: str, filename="debug.log") -> None:
    """Appends debug messages to a log file."""
    log_path = os.path.join(os.getcwd(), filename)  # Save log in the current directory
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


@mcp.tool()
def get_recent_files() -> list[str]:
    """Retrieve the top 20 most recently created or updated files in the directory.

    Returns:
        List of file paths sorted by most recent first.
    """
    if not os.path.exists(SEARCH_DIRECTORY):
        return [f"Error: Directory '{SEARCH_DIRECTORY}' does not exist."]

    recent_files = []

    # Walk through the directory and gather file modification times
    for root, _, files in os.walk(SEARCH_DIRECTORY):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Get file creation and modification time
                mod_time = os.path.getmtime(file_path)
                creation_time = os.path.getctime(file_path)
                latest_time = max(mod_time, creation_time)  # Use the most recent timestamp

                # Maintain a heap for top N recent files
                heapq.heappush(recent_files, (latest_time, file_path))
                if len(recent_files) > TOP_N:
                    heapq.heappop(recent_files)  # Keep only the top N elements
            except Exception as e:
                debug_log(f"Error accessing file {file_path}: {e}")

    # Sort results in descending order (most recent first)
    recent_files = sorted(recent_files, key=lambda x: x[0], reverse=True)

    # Format the output with timestamps
    formatted_results = [
        f"{datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')} - {path}"
        for ts, path in recent_files
    ]

    return formatted_results if formatted_results else ["No files found."]


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
