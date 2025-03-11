"""
Graph builder for LangGraph.
"""
from langgraph.graph import StateGraph, START, END

from graph.state import GraphState
from graph.nodes import initial_invoke, tool_call_and_second_invoke, finalize_answer, conditional_next

def build_graph():
    """
    Builds and compiles the LangGraph.
    
    Returns:
        StateGraph: The compiled graph.
    """
    # Create the graph builder
    builder = StateGraph(GraphState)
    builder.auto_fields = True
    builder.autochannel = True

    # Add nodes
    builder.add_node("InvokeLLM", initial_invoke)
    builder.add_node("ToolCall", tool_call_and_second_invoke)
    builder.add_node("Finalize", finalize_answer)

    # Add edges
    builder.add_edge(START, "InvokeLLM")
    builder.add_conditional_edges("InvokeLLM", conditional_next)
    builder.add_edge("ToolCall", "InvokeLLM")
    builder.add_edge("Finalize", END)

    # Compile the graph
    return builder.compile(checkpointer=None)
