

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
mcp = FastMCP("agentiq_client")

# Alternative: Brave Search API (Recommended)


# Logging setup
logging.basicConfig(
    filename="google_search.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
@mcp.tool()
async def call_agent_iq(question: str, max_results: int = 5) -> List[str]:
    """
    call_agent_iq is a powerful tool that routes any input question to the Agent IQ reasoning engine.

    Agent IQ is an intelligent agent framework designed for advanced reasoning, context enrichment,
    and knowledge-augmented responses. This tool helps agents generate deeper, more insightful answers
    by leveraging Agent IQ's backend through an HTTP API.

    Arguments:
    - question (str): The user query or problem statement to be reasoned upon.
    - max_results (int): (Reserved) Optional limit for response variants or insights. Currently unused.

    Returns:
    - List[str]: A list of enriched, reasoning-backed responses generated by Agent IQ.

    Use this tool when:
    - You need high-quality reasoning or explanations.
    - You want to enhance an existing answer with deeper context.
    - You’re unsure how to respond and want a smart agent to help.

    """
    import logging
   
    logging.info(f"Call help to Agent IQ: {question}")

    import requests
    import json

    url = "http://localhost:5111/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "input_message": question
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    print("Status Code:", response.status_code)
    print("Response:", response.text)
    return response.text

if __name__ == "__main__":
    # Initialize and run the FastMCP server
    mcp.run(transport="stdio")
