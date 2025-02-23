"""Prompt management for the arXiv MCP server."""

from typing import Optional
from .base import PromptManager
from .templates.discovery import research_discovery_prompts
from .templates.analysis import paper_analysis_prompts
from .templates.synthesis import knowledge_synthesis_prompts
from .templates.workflow import research_workflow_prompts

# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get or create the global PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
        # Register all prompts
        for prompt in research_discovery_prompts:
            _prompt_manager.register_template(prompt)
        for prompt in paper_analysis_prompts:
            _prompt_manager.register_template(prompt)
        for prompt in knowledge_synthesis_prompts:
            _prompt_manager.register_template(prompt)
        for prompt in research_workflow_prompts:
            _prompt_manager.register_template(prompt)

    return _prompt_manager
