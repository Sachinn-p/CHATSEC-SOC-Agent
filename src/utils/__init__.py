"""
Utility functions package for SOC Agent Automation.

This package provides datetime utilities, file utilities, and general helper functions.
"""

# Import datetime utilities
from .datetime_utils import (
    timestamp,
    iso_timestamp,
    format_datetime
)

# Import file utilities
from .file_utils import (
    format_file_size,
    ensure_directory_exists,
    safe_read_file
)

# Import general utilities  
from .general import (
    sanitize_filename,
    truncate_text,
    safe_json_loads,
    safe_json_dumps,
    extract_error_message,
    validate_config_dict,
    setup_logging,
    mask_sensitive_data,
    chunk_list,
    flatten_dict,
    deep_merge_dicts,
    HealthChecker,
    get_health_checker
)

__all__ = [
    # Datetime utilities
    'timestamp',
    'iso_timestamp',
    'format_datetime',
    # File utilities
    'format_file_size',
    'ensure_directory_exists',
    'safe_read_file',
    # General utilities
    'sanitize_filename',
    'truncate_text',
    'safe_json_loads',
    'safe_json_dumps',
    'extract_error_message',
    'validate_config_dict',
    'setup_logging',
    'mask_sensitive_data',
    'chunk_list',
    'flatten_dict',
    'deep_merge_dicts',
    'HealthChecker',
    'get_health_checker'
]
