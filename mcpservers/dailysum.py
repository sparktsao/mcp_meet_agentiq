import os
import random
import httpx
import markdown
from datetime import datetime
from typing import Any
from mcp.server.fastmcp import FastMCP
from collections import defaultdict
from markdown2 import markdown as md_to_html
from bs4 import BeautifulSoup

# Initialize FastMCP server
mcp = FastMCP("dailysummary")

from pathlib import Path
OBSIDIAN_VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", "https://api.openai.com/v1"))


def debug_log(message: str, filename="debug.log") -> None:
    """Appends debug messages to a log file."""
    log_path = os.path.join(os.getcwd(), filename)  # Save log in the current directory
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")

import os
import re
from collections import defaultdict


@mcp.tool()
def summarize_obsidian_notes() -> dict:
    """
    Summarize key insights from daily and research notes in the Obsidian vault.
    
    This function scans all markdown files (*.md), extracts summaries, and categorizes them into:
    - "daily_notes": Summarized entries from daily logs (e.g., YYYY-MM-DD.md, 'daily' in filename).
    - "research_notes": Summarized entries from research-related notes.
    - "recent_notes": Notes modified within the last 7 days.

    Returns:
        dict: A dictionary containing categorized summaries of notes.
    """
    summaries = {
        "daily_notes": {},
        "research_notes": {},
        "recent_notes": {}
    }

    if not os.path.exists(OBSIDIAN_VAULT_PATH):
        return {"error": f"Obsidian vault path '{OBSIDIAN_VAULT_PATH}' not found."}

    # Date pattern for daily notes (e.g., 2024-02-22.md)
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

    for root, _, files in os.walk(OBSIDIAN_VAULT_PATH):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as md_file:
                        content = md_file.read()
                        summary = extract_summary_from_markdown(content)

                        # Classify as daily note, research note, or recent note
                        if "daily" in file.lower() or date_pattern.match(file):
                            summaries["daily_notes"][file] = summary
                        elif "research" in root.lower() or "research" in file.lower():
                            summaries["research_notes"][file] = summary
                        if os.path.getmtime(file_path) > (time.time() - 7 * 86400):
                            summaries["recent_notes"][file] = summary
                except Exception as e:
                    summaries["error"] = f"Error processing {file}: {str(e)}"

    return summaries


def extract_summary_from_markdown(content: str) -> str:
    """Extract a summary from markdown text."""
    # Convert Markdown to HTML for better parsing
    html_content = md_to_html(content)
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract first 3 paragraphs or first 300 characters (whichever is shorter)
    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    summary = " ".join(paragraphs[:3])[:300]

    return summary if summary else "No significant content found."



if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
