"""
Main application entry point.

This file serves as the main entry point for the application, importing and using
the modular components defined in the other files.
"""
import os
import sys
import logging
import importlib.util
import pathlib

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

# Import Chainlit handlers
# This will register the Chainlit handlers
from ui.chainlit_handlers import on_chat_start, on_message

# The application will be run using the Chainlit CLI, which will
# automatically discover and use the handlers defined in chainlit_handlers.py

if __name__ == "__main__":
    print("This file is meant to be imported by Chainlit, not run directly.")
    print("Run the application using: chainlit run app/app.py")
    sys.exit(1)
