"""
MCP Tool Manager module.
"""
import os
import json
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import logging
# Logging setting
logger = logging.getLogger(__name__)
grpc_logger = logging.getLogger("grpc")
grpc_logger.setLevel(logging.DEBUG)

class MCPToolManager:
    """
    Manages MCP tool servers and provides an interface for tool invocation.
    """
    def __init__(self, server_configs: List[Dict[str, Any]]):
        self.server_configs = server_configs
        self.tools: Dict[str, Any] = {}
        self.sessions: Dict[str, ClientSession] = {}  # Store persistent sessions
        self.exit_stacks: Dict[str, AsyncExitStack] = {} # Store exit stacks

    async def initialize(self):
        """Initializes all configured servers and stores their sessions."""
        logger.debug("MCP tools configs:")
        for cfg in self.server_configs:
            logger.debug(cfg)
            await self.connect_one_server(cfg)
    
    def get_venv_python(self):
        """Returns the correct Python executable path inside the virtual environment."""
        venv_path = os.sys.prefix  # sys.prefix points to the virtual environment root

        if os.name == "nt":  # Windows
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:  # macOS/Linux
            python_path = os.path.join(venv_path, "bin", "python")

        return python_path if os.path.exists(python_path) else None

    async def connect_one_server(self, cfg: Dict[str, Any]):
        """Establishes a connection to a tool server and initializes tool mappings."""
        name = cfg["name"] # Tool Name (eg. WeatherTool)
        command = cfg["command"]
        args = cfg["args"]

        if command == "python":
            venv_python = self.get_venv_python()
            logger.debug("Current virtual environment's Python interpreter: %s", venv_python)

            if not venv_python:
                logger.error("Error: Could not find the virtual environment's Python interpreter.")
                os.sys.exit(1)

            command = venv_python

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None
        )
        self.exit_stacks[name] = AsyncExitStack()
        stdio_transport = await self.exit_stacks[name].enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        session = await self.exit_stacks[name].enter_async_context(ClientSession(self.stdio, self.write))

        await session.initialize()

        # Store session for future tool calls
        self.sessions[name] = session

        # List available tools
        tool_list_resp = await session.list_tools()
        
        logger.debug("List of MCP Tools:")
        logger.debug(f"\033[91m {tool_list_resp}\033[0m")
        self.tools[name] = tool_list_resp

    async def async_call_tool(self, tool_server: str, tool_name: str, kwargs) -> Any:
        """Calls a tool asynchronously, ensuring the correct session is used."""
        # if tool_name not in self.tools[tool_server]:
        #     raise ValueError(f"Tool '{tool_name}' not found in tool server '{tool_server}'!")

        result = await self.sessions[tool_server].call_tool(tool_name, kwargs)
        logger.debug("Tool result call for Tool server [%s] with Tool [%s]", tool_server, tool_name)
        logger.debug(result)
        return result

    async def call_tool(self, tool_server: str, tool_name: str, kwargs) -> Any:
        """Calls a tool and ensures the result is returned properly."""
        logger.debug(f"MCP call_tool-1: {tool_server}::{tool_name} with args: {kwargs}")

        if tool_server not in self.sessions:
            raise ValueError(f"Tool server '{tool_server}' not found!")

        try:
            result = await self.sessions[tool_server].call_tool(tool_name, kwargs)
            logger.debug(f"MCP call Tool-2: '{tool_name}' execution complete. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            return {"error": str(e)}

    async def cleanup(self):
        """Closes all sessions and exit stacks on shutdown."""
        logger.info("Cleaning up MCP sessions...")
        
        # Close all exit stacks which will properly clean up all resources
        for name, exit_stack in list(self.exit_stacks.items()):
            try:
                await exit_stack.aclose()
                logger.info(f"Successfully closed exit stack for {name}")
            except Exception as e:
                logger.error(f"Error closing exit stack for {name}: {e}")
        
        # Clear all dictionaries
        self.exit_stacks.clear()
        self.sessions.clear()
        self.tools.clear()
        logger.info("MCP cleanup complete")
