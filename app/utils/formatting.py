"""
Formatting utilities for pretty printing messages and responses.
"""
import textwrap
from colorama import Fore, Style
from typing import List, Dict, Any

def pretty_print_long_string(long_string, width=180):
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
    Pretty prints tool response messages with colors for better readability.

    Args:
        messages: The tool response messages to print.

    Returns:
        None
    """
    print(Fore.RED)
    pretty_print_long_string(messages)
    print(Style.RESET_ALL + "-" * 80)  # Separator for clarity
