"""
Debug utility module for controlling debug output throughout the fiscal sustainability model.
"""

import os
import sys

# Global debug setting - can be set from the main notebook
DEBUG_MODE = "OFF"

def set_debug_mode(mode):
    """
    Set the global debug mode.
    
    Args:
        mode (str): Either "ON" or "OFF"
    """
    global DEBUG_MODE
    if mode.upper() in ["ON", "OFF"]:
        DEBUG_MODE = mode.upper()
    else:
        print(f"Warning: Invalid debug mode '{mode}'. Using 'OFF'.")
        DEBUG_MODE = "OFF"

def is_debug_on():
    """
    Check if debug mode is enabled.
    
    Returns:
        bool: True if debug mode is "ON", False otherwise
    """
    return DEBUG_MODE == "ON"

def debug_print(*args, **kwargs):
    """
    Print debug information only if debug mode is enabled.
    
    Args:
        *args: Arguments to pass to print()
        **kwargs: Keyword arguments to pass to print()
    """
    if is_debug_on():
        print(*args, **kwargs)

def debug_print_section(title, char="=", width=60):
    """
    Print a debug section header only if debug mode is enabled.
    
    Args:
        title (str): Section title
        char (str): Character to use for the separator line
        width (int): Width of the separator line
    """
    if is_debug_on():
        print(f"\n{title}")
        print(char * width)

def debug_print_subsection(title, char="-", width=40):
    """
    Print a debug subsection header only if debug mode is enabled.
    
    Args:
        title (str): Subsection title
        char (str): Character to use for the separator line
        width (int): Width of the separator line
    """
    if is_debug_on():
        print(f"\n--- {title} ---")

def debug_print_info(label, value, prefix="  "):
    """
    Print debug information in a formatted way only if debug mode is enabled.
    
    Args:
        label (str): Label for the information
        value: Value to display
        prefix (str): Prefix for the line
    """
    if is_debug_on():
        print(f"{prefix}{label}: {value}")

def debug_print_success(message, prefix="✓ "):
    """
    Print a success message only if debug mode is enabled.
    
    Args:
        message (str): Success message
        prefix (str): Prefix for the message
    """
    if is_debug_on():
        print(f"{prefix}{message}")

def debug_print_warning(message, prefix="⚠️  "):
    """
    Print a warning message only if debug mode is enabled.
    
    Args:
        message (str): Warning message
        prefix (str): Prefix for the message
    """
    if is_debug_on():
        print(f"{prefix}{message}")

def debug_print_error(message, prefix="❌ "):
    """
    Print an error message only if debug mode is enabled.
    
    Args:
        message (str): Error message
        prefix (str): Prefix for the message
    """
    if is_debug_on():
        print(f"{prefix}{message}")

def debug_print_search(label, value, prefix="🔍 "):
    """
    Print a search-related debug message only if debug mode is enabled.
    
    Args:
        label (str): Search label
        value: Search value
        prefix (str): Prefix for the message
    """
    if is_debug_on():
        print(f"{prefix}{label}: {value}")

def debug_print_processing(label, value, prefix="  "):
    """
    Print a processing-related debug message only if debug mode is enabled.
    
    Args:
        label (str): Processing label
        value: Processing value
        prefix (str): Prefix for the message
    """
    if is_debug_on():
        print(f"{prefix}{label}: {value}")

def debug_print_row_info(row_num, **kwargs):
    """
    Print row information only if debug mode is enabled.
    
    Args:
        row_num (int): Row number
        **kwargs: Key-value pairs to display
    """
    if is_debug_on():
        print(f"\n  Row {row_num}:")
        for key, value in kwargs.items():
            print(f"    {key}: '{value}' (type: {type(value)})")

def debug_print_parameter_info(section, param_name, value, distribution=None):
    """
    Print parameter information only if debug mode is enabled.
    
    Args:
        section (str): Parameter section
        param_name (str): Parameter name
        value: Parameter value
        distribution (str, optional): Distribution type
    """
    if is_debug_on():
        if distribution:
            print(f"    ✓ Added {distribution} prior for {param_name}: {value}")
        else:
            print(f"    ✓ Parameter {section}.{param_name}: {value}")

def debug_print_available_items(label, items, prefix="  "):
    """
    Print available items only if debug mode is enabled.
    
    Args:
        label (str): Label for the items
        items: List or iterable of items
        prefix (str): Prefix for the line
    """
    if is_debug_on():
        print(f"{prefix}{label}:")
        for item in items:
            print(f"    {item}")

def debug_print_file_info(file_path, exists=True, prefix="  "):
    """
    Print file information only if debug mode is enabled.
    
    Args:
        file_path (str): File path
        exists (bool): Whether the file exists
        prefix (str): Prefix for the line
    """
    if is_debug_on():
        status = "✓" if exists else "❌"
        print(f"{prefix}{status} File: {file_path}")
        print(f"{prefix}  File exists: {exists}")

def debug_print_counts(label, counts_dict, prefix="  "):
    """
    Print count information only if debug mode is enabled.
    
    Args:
        label (str): Label for the counts
        counts_dict (dict): Dictionary of counts
        prefix (str): Prefix for the line
    """
    if is_debug_on():
        print(f"{prefix}{label}:")
        for key, count in counts_dict.items():
            print(f"    {key}: {count} parameters")
