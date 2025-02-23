import sys
import os
import logging
import asyncio
from typing import List

# Ensure module path is set correctly
sys.path.append('/Users/sparkt/2024_CODE/duoagent/duoagent/')

# Import required modules
import util_wiki
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("wiki")

# Logging setup
LOG_FILE = "mcp_server.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@mcp.tool()
async def wiki_summary(spacekey: str, number_of_day: int = 5) -> List[str]:
    """
    Fetch recent updates from a specified space in Trend Micro Wiki.
    
    Parameters:
    spacekey (str): The unique space key identifier.
    number_of_day (int): Number of days to look back for updates (default: 5).
    
    Returns:
    List[str]: Summary of recent updates.

    Here are the teams mapping from TeamName/Description to spacekey
    spacename,spacekey
    team AILAB, CAL
    team ContentSecurity, CTCS
    team CloudOne, CloudOne
    team ProjectCybertron, PCRY
    team TrendMicroVisionOne, TVO
    team CoreTech, CT
    team SPN, SPN
    team JAG, JAG
    person yaoching_yu, ~63c62d176178fcc941d87a71
    person dennis_tsai, ~622a2bb88a4bb60068f652ce
    person liam_huang, ~60596590109af1006891381e
    person james_chiang, ~7120208ac1f8ffe4aa4d369e56a13fc9ba75eb
    person ageless_kao, ~622a22b74160640069cae769
    person chiachin, ~63902e573c26ca7fa0d6ed66
    """
    try:
        logging.info(f"Fetching updates for space: {spacekey}, last {number_of_day} days.")
        updates_df = util_wiki.get_Space_RecentUpdates(spacekey, number_of_day)
        summary = util_wiki.get_dataframe_summary(updates_df)
        return summary
    except Exception as e:
        logging.error(f"Error in wiki_summary: {e}")
        return ["Error fetching wiki summary. Check logs for details."]

if __name__ == "__main__":
    try:
        logging.info("Starting FastMCP server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logging.critical(f"MCP server failed to start: {e}")
