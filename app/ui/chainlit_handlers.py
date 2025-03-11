"""
Chainlit UI handlers.
"""
import os
import asyncio
import chainlit as cl
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
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "your langfuse secret key"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "your langfuse public key"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

# LLM configuration
LLM_API_ENDPOINT = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY_HERE")
LLM_MODEL = "gpt-4o-mini"

# Load server configuration
SERVERS_CONFIG = load_server_config()

# Create Langfuse handler
langfuse_handler = CallbackHandler()

@cl.on_chat_start
async def on_chat_start():
    """
    Handler for chat start event.
    """
    if cl.user_session.get("initialized"):
        print("[DEBUG] on_chat_start skipped because session is already initialized.")
        return
    
    cl.user_session.set("initialized", True)  # Mark session as initialized

    session_id = cl.user_session.get("session_id")
    if session_id is None:
        session_id = os.urandom(8).hex()  # Generate a unique session ID
        cl.user_session.set("session_id", session_id)

    print(f"[DEBUG] on_chat_start triggered - Session ID: {session_id}")

    # Check if MCP Tool Manager is already initialized
    if cl.user_session.get("tool_manager") is None:
        llm = SingleLLMClient(LLM_API_ENDPOINT, LLM_API_KEY, LLM_MODEL)
        mcp_client = MCPToolManager(SERVERS_CONFIG)
        
        # Run tool manager initialization in the background
        task = asyncio.create_task(mcp_client.initialize())
        await task

        # Store in user session so it's not recreated every time
        cl.user_session.set("llm", llm)
        cl.user_session.set("tool_manager", mcp_client)
        
        # Build the graph
        graph = build_graph()
        cl.user_session.set("graph", graph)

        print("MCPToolManager initialized.")

    else:
        print("MCPToolManager already initialized, skipping.")

    await cl.Message(content="Hello! Ask me anything.").send()

@cl.on_message
async def on_message(msg: cl.Message):
    """
    Handler for incoming messages.
    
    Args:
        msg (cl.Message): The incoming message.
    """
    user_txt = msg.content.strip()
    print(f"Received message: {user_txt}")  # Debug print

    # Create state for this message
    my_state = MyState(user_input=user_txt)
    my_state.llm = cl.user_session.get("llm")
    my_state.tool_manager = cl.user_session.get("tool_manager")

    # Get the graph
    graph = cl.user_session.get("graph")
    
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
        async for output in graph.astream(initial_state, stream_mode="messages", config=config):
            print(f"Stream output: {output}")  # Debug print
            if isinstance(output, dict) and "final_answer" in output:
                final_answer = output["final_answer"]
    except Exception as e:
        print(f"Error in stream: {e}")  # Debug print
        final_answer = f"Error occurred: {str(e)}"

    # If we didn't get a final answer from the graph, check my_state
    if not final_answer:
        final_answer = my_state.final_answer
    
    # If we still don't have an answer, provide a fallback
    if not final_answer:
        final_answer = "I apologize, but I wasn't able to generate a response. Please try again."

    print(f"Sending answer: {final_answer}")  # Debug print
    await cl.Message(content=final_answer).send()
