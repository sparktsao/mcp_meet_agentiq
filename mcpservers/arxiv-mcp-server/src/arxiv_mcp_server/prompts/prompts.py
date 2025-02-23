"""Prompt definitions for arXiv MCP server."""

from mcp.types import (
    Prompt, 
    PromptArgument,
    PromptMessage,
    TextContent,
    GetPromptResult
)

# Define all prompts
PROMPTS = {
    "research-discovery": Prompt(
        name="research-discovery",
        description="Begin research exploration on a specific topic",
        arguments=[
            PromptArgument(name="topic", description="Research topic or question", required=True),
            PromptArgument(name="expertise_level", description="User's familiarity (beginner/intermediate/expert)", required=False),
            PromptArgument(name="time_period", description="Time period for search (e.g., '2023-present')", required=False)
        ]
    ),
    "paper-analysis": Prompt(
        name="paper-analysis", 
        description="Analyze a specific paper",
        arguments=[
            PromptArgument(name="paper_id", description="arXiv paper ID", required=True),
            PromptArgument(name="focus_area", description="Focus area (methodology/results/implications)", required=False)
        ]
    ),
    "literature-synthesis": Prompt(
        name="literature-synthesis",
        description="Synthesize findings across papers",
        arguments=[
            PromptArgument(name="paper_ids", description="List of arXiv paper IDs", required=True),
            PromptArgument(name="synthesis_type", description="Synthesis type (themes/methods/timeline/gaps)", required=False)
        ]
    )
}