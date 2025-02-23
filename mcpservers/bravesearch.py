import os
import random
import httpx
from mcp.server.fastmcp import FastMCP
from typing import Any


# Initialize FastMCP server
mcp = FastMCP("google_search")

# Google Search Alternative (Brave Search API - avoids Google bot detection)
SEARCH_ENGINE_URL = "https://search.brave.com/search?q="

# Most successful User-Agent settings (rotating to avoid anti-crawl)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]


def get_random_user_agent() -> str:
    """Select a random User-Agent string to avoid bot detection."""
    return random.choice(USER_AGENTS)


def debug_log(message: str, filename="debug.log") -> None:
    """Appends debug messages to a log file."""
    log_path = os.path.join(os.getcwd(), filename)  # Save log in the current directory
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


@mcp.tool()
async def google_search(query: str, max_results: int = 5) -> list[str]:
    """Perform a Google-like search using Brave Search.

    Args:
        query: Search term.
        max_results: Number of results to return.

    Returns:
        A list of search result URLs.
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    search_url = f"{SEARCH_ENGINE_URL}{query.replace(' ', '+')}"
    
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
        try:
            response = await client.get(search_url)
            response.raise_for_status()
            
            #Extract news articles
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            import util
            rewrite_version = util.prompt_to_llm(f"Please rewrite to a easy read version:   {soup.text}", model_name="gpt-4o-mini")            
        
            return rewrite_version
            
            return search_results[:max_results]

        except httpx.HTTPStatusError as e:
            debug_log(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            debug_log(f"Error during search: {str(e)}")

    return ["Error performing search."]


def extract_links(html: str) -> list[str]:
    """Extracts search result links from the raw HTML."""
    import re

    # A simple regex-based extraction (works for Brave search)
    pattern = re.compile(r'href="(https?://[^\s"]+)"')
    matches = pattern.findall(html)

    # Filter out unwanted links (ads, tracking, etc.)
    filtered_links = [link for link in matches if not any(
        exclude in link for exclude in ["accounts.google.com", "support.google.com", "policies.google.com"]
    )]

    return filtered_links


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
