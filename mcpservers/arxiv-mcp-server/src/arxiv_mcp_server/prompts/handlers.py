"""Handlers for prompt-related requests."""

from typing import List, Dict
from mcp.types import (
    Prompt,
    PromptMessage,
    TextContent,
    GetPromptResult
)
from .prompts import PROMPTS

async def list_prompts() -> List[Prompt]:
    """Handle prompts/list request."""
    return list(PROMPTS.values())

async def get_prompt(name: str, arguments: Dict[str, str] | None = None) -> GetPromptResult:
    """Handle prompts/get request."""
    if name not in PROMPTS:
        raise ValueError(f"Prompt not found: {name}")
        
    prompt = PROMPTS[name]
    if arguments is None:
        raise ValueError(f"No arguments provided for prompt: {name}")

    # Validate required arguments
    for arg in prompt.arguments:
        if arg.required and (arg.name not in arguments or not arguments.get(arg.name)):
            raise ValueError(f"Missing required argument: {arg.name}")
        
    if name == "research-discovery":
        topic = arguments.get("topic", "")
        expertise = arguments.get("expertise_level", "intermediate")
        time_period = arguments.get("time_period", "")
        
        guide = {
            "beginner": "I'll explain key concepts and methodologies.",
            "intermediate": "We'll focus on recent developments.",
            "expert": "We'll dive deep into technical details."
        }.get(expertise, "We'll focus on recent developments.")
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Help me explore research papers on {topic}. "
                        f"{f'Time period: {time_period}. ' if time_period else ''}"
                        f"{guide}\n\nWhat specific aspects interest you most?"
                    )
                )
            ]
        )

    elif name == "paper-analysis":
        paper_id = arguments.get("paper_id", "")
        focus = arguments.get("focus_area", "complete")
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Analyze paper {paper_id} with a focus on {focus}. "
                        f"Please provide a detailed breakdown of the paper's content, "
                        f"methodology, and key findings."
                    )
                )
            ]
        )
        
    elif name == "literature-synthesis":
        paper_ids = arguments.get("paper_ids", "")
        synthesis_type = arguments.get("synthesis_type", "comprehensive")
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Synthesize the findings from these papers: {paper_ids}. "
                        f"Focus on creating a {synthesis_type} analysis that highlights "
                        f"key themes, methodological approaches, and research implications."
                    )
                )
            ]
        )
    
    raise ValueError("Prompt implementation not found")