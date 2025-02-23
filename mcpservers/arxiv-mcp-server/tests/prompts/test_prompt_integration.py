"""Integration tests for prompt functionality."""

import pytest
from arxiv_mcp_server.server import server

@pytest.mark.asyncio
async def test_server_list_prompts():
    """Test server list_prompts endpoint."""
    prompts = await server.list_prompts()
    assert len(prompts) == 3
    
    # Check that all prompts have required fields
    for prompt in prompts:
        assert prompt.name
        assert prompt.description
        assert prompt.arguments is not None

@pytest.mark.asyncio
async def test_server_get_research_prompt():
    """Test server get_prompt endpoint with research prompt."""
    result = await server.get_prompt(
        name="research-discovery",
        arguments={"topic": "machine learning", "expertise_level": "expert"}
    )
    
    assert len(result.messages) == 1
    message = result.messages[0]
    assert message.role == "user"
    assert "machine learning" in message.content.text
    assert "dive deep" in message.content.text.lower()

@pytest.mark.asyncio
async def test_server_get_analysis_prompt():
    """Test server get_prompt endpoint with analysis prompt."""
    result = await server.get_prompt(
        name="paper-analysis",
        arguments={"paper_id": "2401.00123", "focus_area": "implications"}
    )
    
    assert len(result.messages) == 1
    message = result.messages[0]
    assert message.role == "user"
    assert "2401.00123" in message.content.text
    assert "implications" in message.content.text.lower()

@pytest.mark.asyncio
async def test_server_get_synthesis_prompt():
    """Test server get_prompt endpoint with synthesis prompt."""
    paper_ids = "2401.00123, 2401.00124"
    result = await server.get_prompt(
        name="literature-synthesis",
        arguments={"paper_ids": paper_ids, "synthesis_type": "timeline"}
    )
    
    assert len(result.messages) == 1
    message = result.messages[0]
    assert message.role == "user"
    assert paper_ids in message.content.text
    assert "timeline" in message.content.text.lower()

@pytest.mark.asyncio
async def test_server_get_prompt_invalid_name():
    """Test server get_prompt endpoint with invalid prompt name."""
    with pytest.raises(ValueError, match="Prompt not found"):
        await server.get_prompt(name="invalid-prompt", arguments={})

@pytest.mark.asyncio
async def test_server_get_prompt_missing_args():
    """Test server get_prompt endpoint with missing required arguments."""
    with pytest.raises(ValueError, match="Missing required argument"):
        await server.get_prompt(name="research-discovery", arguments={})