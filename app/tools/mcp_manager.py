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
logging.basicConfig(level=logging.DEBUG)
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
        print("INIT MCP TOOL MANAGER")
        for cfg in self.server_configs:
            print("for each MCP server!")
            print(cfg)
            await self.connect_one_server(cfg)

    async def connect_one_server(self, cfg: Dict[str, Any]):
        """Establishes a connection to a tool server and initializes tool mappings."""
        name = cfg["name"] # Tool Name (eg. WeatherTool)
        command = cfg["command"]
        args = cfg["args"]

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
        
        print("TOOLS")
        print(f"\033[91m {tool_list_resp}\033[0m")
        self.tools[name] = tool_list_resp

    async def async_call_tool(self, tool_server: str, tool_name: str, kwargs) -> Any:
        """Calls a tool asynchronously, ensuring the correct session is used."""
        # if tool_name not in self.tools[tool_server]:
        #     raise ValueError(f"Tool '{tool_name}' not found in tool server '{tool_server}'!")

        result = await self.sessions[tool_server].call_tool(tool_name, kwargs)
        print("ASYNC RESULT")
        print(result)
        return result

    async def call_tool(self, tool_server: str, tool_name: str, kwargs) -> Any:
        """Calls a tool and ensures the result is returned properly."""
        print(f"MCP call_tool-1: {tool_server}::{tool_name} with args: {kwargs}")

        if tool_server not in self.sessions:
            raise ValueError(f"Tool server '{tool_server}' not found!")

        try:
            result = await self.sessions[tool_server].call_tool(tool_name, kwargs)
            print(f"MCP call Tool-2: '{tool_name}' execution complete. Result: {result}")
            return result
        except Exception as e:
            print(f"Error calling tool '{tool_name}': {e}")
            return {"error": str(e)}

    async def cleanup(self):
        """Closes all sessions and exit stacks on shutdown."""
        print("Cleaning up MCP sessions...")
        
        # Close all exit stacks which will properly clean up all resources
        for name, exit_stack in list(self.exit_stacks.items()):
            try:
                await exit_stack.aclose()
                print(f"Successfully closed exit stack for {name}")
            except Exception as e:
                print(f"Error closing exit stack for {name}: {e}")
        
        # Clear all dictionaries
        self.exit_stacks.clear()
        self.sessions.clear()
        self.tools.clear()
        print("MCP cleanup complete")
