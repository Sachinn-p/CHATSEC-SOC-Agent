"""
DateTime utility functions for SOC Agent Automation.
"""
from datetime import datetime
from typing import Optional


def timestamp() -> str:
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def iso_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def format_datetime(dt_string: str, format_out: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime string to desired format
    
    Args:
        dt_string: Input datetime string
        format_out: Desired output format
        
    Returns:
        Formatted datetime string or original if parsing fails
    """
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime(format_out)
    except (ValueError, AttributeError, TypeError):
        return dt_string