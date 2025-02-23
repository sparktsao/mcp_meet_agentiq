import os
import random
import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from typing import List, Dict

# Initialize FastMCP server
mcp = FastMCP("news_search")

# Google News Search URL
GOOGLE_NEWS_SEARCH_URL = "https://news.google.com/search?q="

# Rotating User-Agent to bypass anti-crawl
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]


def get_random_user_agent() -> str:
    """Select a random User-Agent string to avoid bot detection."""
    return random.choice(USER_AGENTS)


import asyncio
async def safe_print(msg):
    print(msg)
    await asyncio.sleep(0)  # Yield control to event loop


@mcp.tool()
def news_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Perform a Google News search and return news headlines with URLs.

    Args:
        query: Search term.
        max_results: Number of news articles to return.

    Returns:
        A list of dictionaries containing article titles and URLs.
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://news.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    search_url = f"{GOOGLE_NEWS_SEARCH_URL}{query.replace(' ', '%20')}"

    try:
        response = httpx.get(search_url, headers=headers, follow_redirects=True, timeout=10.0)
        response.raise_for_status()

        # Extract news articles
        soup = BeautifulSoup(response.text, "html.parser")
        
        return soup.text

    except httpx.HTTPStatusError as e:
        return [{"title": f"HTTP error: {e.response.status_code}", "url": ""}]
    except Exception as e:
        return [{"title": f"Error: {str(e)}", "url": ""}]


def extract_news_articles(html: str) -> List[Dict[str, str]]:
    """Extracts news article titles and URLs from Google News Search results."""
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Extracting articles from Google News
    for article in soup.find_all("article"):
        title_tag = article.find("h3")
        link_tag = article.find("a", href=True)

        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            url = "https://news.google.com" + link_tag["href"][1:]  # Remove leading '.' in relative URL
            articles.append({"title": title, "url": url})

    return articles


if __name__ == "__main__":
    # Start MCP server in sync mode
    mcp.run(transport="stdio")
