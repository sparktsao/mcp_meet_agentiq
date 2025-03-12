"""
Formatting utilities for pretty printing messages and responses.
"""
import textwrap
from colorama import Fore, Style
from typing import List, Dict, Any
import io
import sys
import logging

# Logging setting
logger = logging.getLogger(__name__)

def capture_print_output(func, *args, **kwargs):
    """
    Captures all `print()` output from a function and returns it as a string.
    """
    # Redirect stdout to capture printed output
    captured_output = io.StringIO()
    sys.stdout = captured_output  # Temporarily redirect stdout

    try:
        func(*args, **kwargs)  # Call the function
    finally:
        sys.stdout = sys.__stdout__  # Restore stdout

    return captured_output.getvalue().strip()  # Get captured output as a string

def pretty_print_long_string(long_string, width=180):
    return capture_print_output(pretty_print_long_string_raw, long_string, width)

def pretty_print_long_string_raw(long_string, width=180):
    """
    Pretty prints a long string in a readable format with specified width.

    Args:
        long_string (str): The long string to pretty print.
        width (int): The width to wrap the string. Default is 180.
        
    Returns:
        None: Prints the formatted string.
    """
    long_string = str(long_string)
    wrapped_string = textwrap.fill(long_string, width=width)
    print(wrapped_string)

def pretty_print(messages):
    return capture_print_output(pretty_print_raw, messages)

def pretty_print_raw(messages):
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
    return capture_print_output(print_tool_response_raw, messages)

def print_tool_response_raw(messages):
    """
    Pretty prints tool response messages with colors for better readability.

    Args:
        messages: The tool response messages to print.

    Returns:
        None
    """
    print(Fore.RED)
    pretty_print_long_string(messages)
    print(Style.RESET_ALL + "-" * 80)  # Separator for clarity
