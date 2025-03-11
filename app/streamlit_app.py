"""
Streamlit application entry point.

This file serves as the entry point for the Streamlit version of the application,
importing and using the modular components defined in the other files.
"""
import os
import sys
import asyncio
import logging
import pathlib
import streamlit as st
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
grpc_logger = logging.getLogger("grpc")
grpc_logger.setLevel(logging.DEBUG)

# Import environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the parent directory to sys.path to enable imports
current_dir = pathlib.Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import Streamlit handlers
from ui.streamlit_handlers import initialize_session, process_message

# Set page configuration
st.set_page_config(
    page_title="Awe Assistant",
    page_icon="🤖",
    layout="wide",
)

# Create a single event loop for the application
if not hasattr(st.session_state, "event_loop"):
    st.session_state.event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.event_loop)

# Helper function to run async functions using the shared event loop
def run_async(async_func, *args, **kwargs):
    loop = st.session_state.event_loop
    return loop.run_until_complete(async_func(*args, **kwargs))

# Initialize session state - ensure it completes before proceeding
if "initialized" not in st.session_state:
    with st.spinner("Initializing session..."):
        run_async(initialize_session)

# Display header
st.title("Awe Assistant")
st.markdown("Ask me anything and I'll help you find answers!")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response with a spinner while processing
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_async(process_message, prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
