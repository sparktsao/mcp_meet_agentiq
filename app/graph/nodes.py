"""
Node functions for LangGraph.
"""
from typing import Dict, Any
from dataclasses import asdict

from langgraph.types import Command

from graph.state import GraphState, MyState
from utils.prompts import generate_system_prompt
from utils.parsing import parse_ai_response
from utils.formatting import pretty_print, print_tool_response
import logging

# Logging setting
logger = logging.getLogger(__name__)

async def initial_invoke(state: GraphState, config: dict):
    """
    Initial node function that invokes the LLM with the user input.
    
    Args:
        state (GraphState): The current graph state.
        config (dict): Configuration including the MyState instance.
        
    Returns:
        Command: Update command with the new state.
    """
    my_state: MyState = config["configurable"]["my_state"]
    tm = my_state.tool_manager
    llm = my_state.llm

    if not hasattr(my_state, "chat_history") or my_state.chat_history is None:
        my_state.chat_history = []

    # Generate the system prompt dynamically
    system_prompt = generate_system_prompt(tm)
    
    if len(my_state.chat_history) > 10:
        call_message = [
            *(my_state.chat_history[-10:]),
            {"role": "user", "content": my_state.user_input}
        ]    
    else:
        call_message = [
            {"role": "system", "content": system_prompt},
            *(my_state.chat_history[-10:]),
            {"role": "user", "content": my_state.user_input}
        ]

    logger.debug("---")
    logger.debug("# of chat_history: %s", len(my_state.chat_history))
    logger.debug("Call LLM Messages:")
    logger.debug("%s", pretty_print(call_message))
    logger.debug("---")

    content = llm.invoke(call_message)

    need_tool, tool_server, tname, targs, final_ans = parse_ai_response(content)

    logger.debug("---")
    logger.debug("Call LLM Responses:")
    logger.debug(content)
    logger.debug("need_tool: %s", need_tool)
    logger.debug("---")

    # Update chat history based on response
    if need_tool is not None:
        if need_tool == False:
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
    """
    Node function that calls a tool and updates the state with the result.
    
    Args:
        state (GraphState): The current graph state.
        config (dict): Configuration including the MyState instance.
        
    Returns:
        Command: Update command with the new state.
    """
    my_state: MyState = config["configurable"]["my_state"]
    tm = my_state.tool_manager
    
    # Initialize the tool server in the usage counts dictionary if it doesn't exist
    if state.tool_server not in my_state.tool_usage_counts:
        my_state.tool_usage_counts[state.tool_server] = {}
    
    # Initialize the tool name in the usage counts dictionary if it doesn't exist
    if state.tool_name not in my_state.tool_usage_counts[state.tool_server]:
        my_state.tool_usage_counts[state.tool_server][state.tool_name] = 0
    
    # Check if the tool has reached its usage limit
    if my_state.tool_usage_counts[state.tool_server][state.tool_name] >= my_state.max_tool_uses:
        # Tool limit reached, return a message instead of calling the tool
        tool_res_str = f"Tool usage limit reached: {state.tool_name} can only be used {my_state.max_tool_uses} times."
        logger.warning(tool_res_str)
    else:
        # Increment the tool usage counter
        my_state.tool_usage_counts[state.tool_server][state.tool_name] += 1
        
        # Log the current tool usage
        logger.info(f"Tool usage: {state.tool_server}.{state.tool_name} - " +
                    f"{my_state.tool_usage_counts[state.tool_server][state.tool_name]}/{my_state.max_tool_uses}")
        
        # Call the tool
        tool_res = await tm.call_tool(state.tool_server, state.tool_name, state.tool_arguments)
        
        logger.info("---")
        logger.info("Tool response:")
        logger.info("%s", print_tool_response(tool_res))
        logger.info("---")

        # Convert tool_res to a string before using it
        if hasattr(tool_res, "content"):
            tool_res_str = "\n".join(content.text for content in tool_res.content)
        else:
            tool_res_str = str(tool_res)  # Fallback if `content` is not present
    
    my_state.chat_history.append({"role": "assistant", "content": f"Tool result from {state.tool_server} {state.tool_name} using {state.tool_arguments} below:"})
    my_state.chat_history.append({"role": "assistant", "content": tool_res_str})
    
    return Command(update=asdict(GraphState(
        tool_invocation_needed=False,
        tool_name=None,
        tool_arguments=None,
        tool_result=tool_res_str        
    )))

def finalize_answer(state: GraphState, config: dict):
    """
    Node function that finalizes the answer.
    
    Args:
        state (GraphState): The current graph state.
        config (dict): Configuration including the MyState instance.
        
    Returns:
        dict: The final answer.
    """
    my_state: MyState = config["configurable"]["my_state"]
    my_state.final_answer = state.final_answer
    logger.debug(f"Finalizing answer: {state.final_answer}")  # Debug print
    return {"final_answer": state.final_answer}

def conditional_next(state: GraphState, config: dict) -> str:
    """
    Conditional edge function that determines the next node based on the state.
    
    Args:
        state (GraphState): The current graph state.
        config (dict): Configuration.
        
    Returns:
        str: The name of the next node or END.
    """
    from langgraph.graph import END
    
    if state.tool_invocation_needed is None:
        return "InvokeLLM"
    if state.tool_invocation_needed:
        return "ToolCall"
    else:
        return END
