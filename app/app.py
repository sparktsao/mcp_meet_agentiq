import os
import json
import asyncio
import chainlit as cl
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
load_dotenv()

from langfuse import Langfuse

langfuse = Langfuse(
  secret_key=os.getenv("LANGFUSE_SECRET_KEY", "your langfuse secret key"),
  public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "your langfuse public key"),
  host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

from langfuse.callback import CallbackHandler

import sys

import requests

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

import logging
logging.basicConfig(level=logging.DEBUG)
grpc_logger = logging.getLogger("grpc")
grpc_logger.setLevel(logging.DEBUG)

# LangGraph
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from dotenv import load_dotenv
load_dotenv()

LLM_API_ENDPOINT = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY_HERE")
LLM_MODEL = "gpt-4o-mini"

###############################################################################
# 1) Single LLM Client
###############################################################################
class SingleLLMClient:
    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4o"):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model

    def invoke(self, messages: List[Dict[str, str]]) -> str:
        print()
        print("invoke:", self.model)
        print(f"\033[33m {messages} \033[0m")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        r = requests.post(f"{self.endpoint}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        print()
        print(f"\033[35m {data} \033[0m")
        return data["choices"][0]["message"]["content"]

###############################################################################
# 2) MCP Tool Manager
###############################################################################
class MCPToolManager:
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
        """Closes all sessions on shutdown."""
        for session in self.sessions.values():
            await session.__aexit__(None, None, None)
        self.sessions.clear()

###############################################################################
# 3) States
###############################################################################
class MyState:
    def __init__(
        self,
        user_input: str,
        tool_invocation_needed: bool = False,
        tool_server: str = "",
        tool_name: str = "",
        tool_arguments: Optional[Dict[str, Any]] = None,
        tool_result: str = "",
        final_answer: str = ""
    ):
        self.user_input = user_input
        self.tool_invocation_needed = tool_invocation_needed
        self.tool_server = tool_server
        self.tool_name = tool_name
        self.tool_arguments = tool_arguments or {}
        self.tool_result = tool_result
        self.final_answer = final_answer

        self.llm: Optional[SingleLLMClient] = None
        self.tool_manager: Optional[MCPToolManager] = None

@dataclass
class GraphState:
    tool_invocation_needed: bool = False
    tool_server: str = ""
    tool_name: str = ""
    tool_arguments: Dict[str, Any] = None
    tool_result: str = ""
    final_answer: str = ""

    def __post_init__(self):
        if self.tool_arguments is None:
            self.tool_arguments = {}

###############################################################################
# 4) Prompt + Helpers
###############################################################################
def generate_system_prompt(tool_manager: MCPToolManager) -> str:
    """Generates a system prompt that includes available tools categorized by server, including input schemas."""

    tool_section = []

    # Organize tools by server
    for tool_name, tool_info in tool_manager.tools.items():
        tool_section.append(tool_name)  # Append tool name as a string

        # Convert tool_info (a dict) into a readable string
        tool_section.append(f"  {tool_info}")  # Indented description for readability
        
    formatted_tool_section = "\n".join(tool_section)
    PROMPT = open("./prompts/prompt_p.txt").read()
    return PROMPT.format(formatted_tool_section=formatted_tool_section)
    
def parse_ai_response(content: str):
    """
    Parses the AI response and extracts relevant fields.

    Args:
        content (str): The raw response from the AI.

    Returns:
        tuple: (need_tool, tool_name, tool_args, final_answer)
    """
    try:
        # Try to parse the response as JSON
        response_data = json.loads(content)

        # Extract tool invocation details
        need_tool = response_data.get("tool_call", False)
        tool_server = response_data.get("tool_server", None)
        tool_name = response_data.get("tool", None)
        tool_args = response_data.get("tool_args", {}) if need_tool else None

        rdata = response_data.get("response", "")
        if type(rdata ) is list:
            rdata = "\n".join([str(x) for x in rdata])
        elif type(rdata) is dict:
            rdata = str(rdata)

        #print()
        #print("rdata", type(rdata), rdata)

        # Extract the final response (if no tool call is needed)
        final_answer = rdata.strip() #if not need_tool else None

        return need_tool, tool_server, tool_name, tool_args, final_answer

    except json.JSONDecodeError:
        # If the AI returned invalid JSON, treat it as a direct response
        print("Loading AI JSON response failed!!!")
        print(content)
        return None, None, None, None, content.strip()
    
      
import textwrap
import textwrap
from colorama import Fore, Style

def pretty_print_long_string(long_string, width=180):
    """
    Pretty prints a long string in a readable format with specified width.

    Args:
        long_string (str): The long string to pretty print.
        width (int): The width to wrap the string. Default is 80.
        
    Returns:
        None: Prints the formatted string.
    """
    long_string = str(long_string)
    wrapped_string = textwrap.fill(long_string, width=width)
    print(wrapped_string)

def pretty_print(messages):
    """
    Pretty prints a list of OpenAI chat messages with colors for better readability.

    Args:
        messages (list): A list of dictionaries, each containing 'role' and 'content'.

    Returns:
        None
    """
    for message in messages:
        role = message["role"]
        content = message["content"]

        # Assign colors based on role
        if role == "system":
            role_color = Fore.BLUE
        elif role == "user":
            role_color = Fore.GREEN
        elif role == "assistant":
            role_color = Fore.YELLOW
        else:
            role_color = Fore.WHITE  # Default color

        print(f"{role_color}Role: {role}{Style.RESET_ALL}")
        print(Fore.CYAN + "Content:" + Style.RESET_ALL)
        pretty_print_long_string(content)
        print(Style.RESET_ALL + "-" * 80)  # Separator for clarity



def print_tool_response(messages):
    """
    Pretty prints a list of OpenAI chat messages with colors for better readability.

    Args:
        messages (list): A list of dictionaries, each containing 'role' and 'content'.

    Returns:
        None
    """
    role_color = Fore.RED  # Default color

    print(Fore.RED)
    pretty_print_long_string(messages)
    print(Style.RESET_ALL + "-" * 80)  # Separator for clarity        

###############################################################################
# 5) Node Functions
###############################################################################
def initial_invoke(state: GraphState, config: dict):
    my_state: MyState = config["configurable"]["my_state"]
    tm = my_state.tool_manager
    llm = my_state.llm

    if not hasattr(my_state, "chat_history") or my_state.chat_history is None:
        my_state.chat_history = []


    # Generate the system prompt dynamically
    system_prompt = generate_system_prompt(tm)
    
    warning_text = "(check the chat history and make sure every tool just use once.)"
    prefix_response = "I will do the response properly based on the conversation"

    if len(my_state.chat_history)>10:
        call_message = [
            *my_state.chat_history, 
            {"role": "user", "content": my_state.user_input}
        ]    
    else:
        call_message = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": my_state.user_input},
            *my_state.chat_history
            
        ]

    print()
    print("# of chat_history:", len(my_state.chat_history))
    print("Call LLM Messages:")
    pretty_print(call_message)
    print()

    content = llm.invoke(call_message)

    need_tool, tool_server, tname, targs, final_ans = parse_ai_response(content)

    print()
    print("Call LLM Responses:")
    print(content)
    print("need_tool", need_tool)#, tool_server, tname, targs, final_ans)
    print()


    # Spark
    if not need_tool is None:
        if need_tool == False:
            my_state: MyState = config["configurable"]["my_state"]
            state.final_answer = final_ans
            my_state.final_answer = final_ans
            # Append new interaction to chat history
            my_state.chat_history.append({"role": "assistant", "content": final_ans})
        else:
            my_state.chat_history.append({"role": "assistant", "content": final_ans})


    return Command(update=asdict(GraphState(
        tool_invocation_needed=need_tool,
        tool_server=tool_server,
        tool_name=tname,
        tool_arguments=targs,
        final_answer=final_ans
    )))

async def tool_call_and_second_invoke(state: GraphState, config: dict):
    
    my_state: MyState = config["configurable"]["my_state"]
    tm = my_state.tool_manager
    llm = my_state.llm

    tool_res = await tm.call_tool(state.tool_server, state.tool_name, state.tool_arguments)
    #tool_res_str = json.dumps(tool_res)
    print()
    print("TOOL RESPONSE:")
    print_tool_response(tool_res)

    # ✅ Convert tool_res to a string before using it
    if hasattr(tool_res, "content"):
        tool_res_str = "\n".join(content.text for content in tool_res.content)
    else:
        tool_res_str = str(tool_res)  # Fallback if `content` is not present

    
    my_state.chat_history.append({"role": "assistant", "content": f"Tool result from {state.tool_server} { state.tool_name}  using {state.tool_arguments} below:"})
    my_state.chat_history.append({"role": "assistant", "content": tool_res_str})
    
    # need_tool, tname, targs, final_ans = parse_ai_response(content)

    return Command(update=asdict(GraphState(
        tool_invocation_needed=False,
        tool_name=None,
        tool_arguments=None,
        tool_result=tool_res_str        
    )))

def finalize_answer(state: GraphState, config: dict):
    my_state: MyState = config["configurable"]["my_state"]
    my_state.final_answer = state.final_answer
    print(f"Finalizing answer: {state.final_answer}")  # Debug print
    return {"final_answer": state.final_answer}

###############################################################################
# 6) Build Graph
###############################################################################
builder = StateGraph(GraphState)
builder.auto_fields = True
builder.autochannel = True


builder.add_node("InvokeLLM", initial_invoke)
builder.add_node("ToolCall", tool_call_and_second_invoke)
builder.add_node("Finalize", finalize_answer)

def conditional_next(state: GraphState, config: dict) -> str:
    if state.tool_invocation_needed is None:
        return "InvokeLLM"
    if state.tool_invocation_needed:
        return "ToolCall"
    else:
        return END
    
builder.add_edge(START, "InvokeLLM")
builder.add_conditional_edges("InvokeLLM", conditional_next)
builder.add_edge("ToolCall", "InvokeLLM")
builder.add_edge("Finalize", END)

graph = builder.compile(checkpointer=None)

###############################################################################
# 7) Chainlit
###############################################################################


# Load Server Configuration from External File
CONFIG_FILE_PATH = "config.json"

def load_server_config():
    """Loads server configurations from an external JSON file."""
    if not os.path.exists(CONFIG_FILE_PATH):
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE_PATH}' not found.")
    
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    print(config_data)
    
    return config_data.get("servers", [])

SERVERS_CONFIG = load_server_config()


@cl.on_chat_start
async def on_chat_start():

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

        print("MCPToolManager initialized.")

    else:
        print("MCPToolManager already initialized, skipping.")

    await cl.Message(content="Hello! Ask me anything.").send()

langfuse_handler = CallbackHandler()

@cl.on_message
async def on_message(msg: cl.Message):
    user_txt = msg.content.strip()
    print(f"Received message: {user_txt}")  # Debug print

    my_state = MyState(user_input=user_txt)
    my_state.llm = cl.user_session.get("llm")
    my_state.tool_manager = cl.user_session.get("tool_manager")

    initial_state = GraphState()
    
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