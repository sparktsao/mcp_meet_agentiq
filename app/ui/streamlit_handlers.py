"""
Streamlit UI handlers.
"""
import os
import asyncio
import streamlit as st
from typing import Dict, Any

from langfuse import Langfuse
from langfuse.callback import CallbackHandler

from config.loader import load_server_config
from tools.llm_client import SingleLLMClient
from tools.mcp_manager import MCPToolManager
from graph.state import MyState, GraphState
from graph.builder import build_graph

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# Langfuse setup
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

# LLM configuration
LLM_API_ENDPOINT = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o-mini"

# Load server configuration
SERVERS_CONFIG = load_server_config()

# Create Langfuse handler
langfuse_handler = CallbackHandler()

async def cleanup_previous_session():
    """
    Clean up resources from a previous session if they exist.
    """
    if "tool_manager" in st.session_state and st.session_state.tool_manager:
        try:
            print("Cleaning up previous MCP sessions...")
            await st.session_state.tool_manager.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")

async def initialize_session():
    """
    Initialize the session state with necessary components.
    """
    # Clean up previous session if it exists
    await cleanup_previous_session()
    
    # Set initialized flag and create new session ID
    st.session_state.initialized = True
    st.session_state.session_id = os.urandom(8).hex()
    st.session_state.chat_history = []
    
    # Initialize LLM client
    st.session_state.llm = SingleLLMClient(LLM_API_ENDPOINT, LLM_API_KEY, LLM_MODEL)
    
    # Initialize MCP Tool Manager with the current event loop
    st.session_state.tool_manager = MCPToolManager(SERVERS_CONFIG)
    
    try:
        await st.session_state.tool_manager.initialize()
    except Exception as e:
        print(f"Error initializing MCP Tool Manager: {e}")
        st.error(f"Failed to initialize MCP tools: {e}")
    
    # Build the graph
    st.session_state.graph = build_graph()
    
    print(f"Session initialized with ID: {st.session_state.session_id}")

async def process_message(user_input: str):
    """
    Process a user message through the LangGraph.
    
    Args:
        user_input (str): The user's input message.
        
    Returns:
        str: The assistant's response.
    """
    # Ensure session is initialized
    if "initialized" not in st.session_state or not st.session_state.initialized:
        await initialize_session()
        
    # Check if required session state variables exist
    required_vars = ["llm", "tool_manager", "chat_history", "graph"]
    for var in required_vars:
        if var not in st.session_state:
            await initialize_session()
            break
    
    # Create state for this message
    my_state = MyState(user_input=user_input)
    my_state.llm = st.session_state.llm
    my_state.tool_manager = st.session_state.tool_manager
    my_state.chat_history = st.session_state.chat_history.copy()
    
    # Get the graph
    graph = st.session_state.graph
    
    # Initial state
    initial_state = GraphState()
    
    # Configuration for the graph
    config = {
        "configurable": {
            "my_state": my_state
        },
        "callbacks": [langfuse_handler]
    }

    final_answer = None
    try:
        # Process the message through the graph
        async for output in graph.astream(initial_state, stream_mode="messages", config=config):
            if isinstance(output, dict) and "final_answer" in output:
                final_answer = output["final_answer"]
    except Exception as e:
        print(f"Error in stream: {e}")
        final_answer = f"Error occurred: {str(e)}"

    # If we didn't get a final answer from the graph, check my_state
    if not final_answer:
        final_answer = my_state.final_answer
    
    # If we still don't have an answer, provide a fallback
    if not final_answer:
        final_answer = "I apologize, but I wasn't able to generate a response. Please try again."
    
    # Update the session chat history with the new interaction
    st.session_state.chat_history = my_state.chat_history
    
    return final_answer
