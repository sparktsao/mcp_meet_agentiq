import os
import random
import asyncio
import httpx
import logging
import json
from typing import List
from bs4 import BeautifulSoup
from time import sleep

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("google_search")

# Alternative: Brave Search API (Recommended)
SEARCH_ENGINE_URL = "https://www.google.com.tw/search?q="

# Rotating User-Agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

# Logging setup
logging.basicConfig(
    filename="google_search.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_random_user_agent() -> str:
    """Select a random User-Agent to prevent detection."""
    return random.choice(USER_AGENTS)

def random_delay(min_wait: float = 2.0, max_wait: float = 7.0) -> None:
    """Introduce a random delay between requests to mimic human behavior."""
    sleep(random.uniform(min_wait, max_wait))

async def fetch_page(query: str) -> str:
    """Fetch search results page with error handling and retries."""
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    
    search_url = f"{SEARCH_ENGINE_URL}{query.replace(' ', '+')}"
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = await client.get(search_url)
                response.raise_for_status()

                # Check for CAPTCHA detection (Google reCAPTCHA)
                if "Our systems have detected unusual traffic" in response.text or "verify you're not a robot" in response.text:
                    logging.warning(f"CAPTCHA detected on attempt {attempt+1}. Retrying after delay.")
                    await asyncio.sleep(random.uniform(30, 60))  # Longer delay before retrying
                    continue  # Retry request
                
                return response.text

            except httpx.HTTPStatusError as e:
                logging.warning(f"HTTP error {e.response.status_code} on attempt {attempt+1} for query: {query}")
                if e.response.status_code in {429, 503}:  # Too many requests or service unavailable
                    await asyncio.sleep(random.uniform(10, 20))  # Wait before retrying

            except httpx.RequestError as e:
                logging.error(f"Request error on attempt {attempt+1}: {e}")
                await asyncio.sleep(5)

    logging.error(f"Failed to fetch search results for query: {query}")
    return ""

def extract_links(html: str) -> List[str]:
    """Extract valid search result links from Google search HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    
    for a_tag in soup.select("a[href]"):
        href = a_tag["href"]
        if href.startswith("/url?q="):  # Google-style result links
            link = href.split("&")[0].replace("/url?q=", "")
            if "google.com" not in link:  # Avoid Google internal links
                links.append(link)
    
    return links

@mcp.tool()
async def google_search(query: str, max_results: int = 5) -> List[str]:
    """Perform a Google search and return a list of result URLs."""
    logging.info(f"Performing Google search for: {query}")
    
    html = await fetch_page(query)

    if not html:
        return ["Failed to fetch results. Google may have blocked the request."]

    soup = BeautifulSoup(html, "html.parser")

    # Detect CAPTCHA challenge
    if "verify you're not a robot" in soup.text or "Our systems have detected unusual traffic" in soup.text:
        logging.warning("Google CAPTCHA detected. Search aborted.")
        return ["Google CAPTCHA detected. Try again later."]

    import util
    rewrite_version = util.prompt_to_llm(
        f"Please rewrite to a easy read version: {soup.text}",
        model_name="gpt-4o-mini"
    )

    return rewrite_version

if __name__ == "__main__":
    # Initialize and run the FastMCP server
    mcp.run(transport="stdio")
