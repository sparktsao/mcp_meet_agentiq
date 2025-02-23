

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
mcp = FastMCP("ai_thinking")

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
@mcp.tool()
async def risk_thinking(question: str, max_results: int = 5) -> List[str]:
    """
    Perform Risk thinking process to generate retrospective ideas.
    Including vulnerability, attack surface, MITRE attack metrics, AI risk
    This tool helps the cybersecurity domain fine-tuned AI LLM analyze complex or uncertain queries
    and refine responses based on additional contextual reasoning.
    """
    import logging
    import util

    logging.info(f"Performing Risk thinking for: {question}")

    prompt = (
        f"You are a cybersecurity fine-tuned AI with specialized knowledge. including vulnerability, attack surface, MITRE attack metrics, AI risk"
        f" The user’s question requires additional reasoning: {question}\n"
        f"Please analyze it thoroughly and generate {max_results} structured insights."
    )

    response = util.prompt_to_llm(prompt, model_name="gpt-4o-mini")

    return response

if __name__ == "__main__":
    # Initialize and run the FastMCP server
    mcp.run(transport="stdio")
