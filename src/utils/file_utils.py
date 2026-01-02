"""
File system utility functions for SOC Agent Automation.
"""
from typing import Optional
import os


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes < 0:
        return "0 B"
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.2f} {size_names[i]}"


def ensure_directory_exists(directory: str) -> bool:
    """Ensure directory exists, create if not
    
    Args:
        directory: Directory path
        
    Returns:
        True if directory exists or was created
    """
    if not directory:
        return False
        
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def safe_read_file(filepath: str, default: Optional[str] = None) -> Optional[str]:
    """Safely read file contents
    
    Args:
        filepath: Path to file
        default: Default value if read fails
        
    Returns:
        File contents or default
    """
    if not filepath or not os.path.exists(filepath):
        return default
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, PermissionError, UnicodeDecodeError):
        return default
