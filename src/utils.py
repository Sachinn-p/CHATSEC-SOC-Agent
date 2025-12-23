"""
Utility functions for SOC Agent Automation.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import re


def timestamp() -> str:
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def iso_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def format_datetime(dt_string: str, format_out: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime string to desired format"""
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime(format_out)
    except ValueError:
        return dt_string


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely dump data to JSON string with fallback"""
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return default


def extract_error_message(exception: Exception) -> str:
    """Extract clean error message from exception"""
    error_msg = str(exception)
    if not error_msg:
        error_msg = exception.__class__.__name__
    return error_msg


def validate_config_dict(config: Dict[str, Any], required_keys: List[str]) -> List[str]:
    """Validate configuration dictionary for required keys"""
    missing_keys = []
    for key in required_keys:
        if key not in config or config[key] is None:
            missing_keys.append(key)
    return missing_keys


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string
    )
    
    return logging.getLogger(__name__)


def mask_sensitive_data(text: str, patterns: Optional[List[str]] = None) -> str:
    """Mask sensitive data in text using regex patterns"""
    if patterns is None:
        patterns = [
            r'password["\s]*[:=]["\s]*([^"\s,}]+)',  # password fields
            r'api_key["\s]*[:=]["\s]*([^"\s,}]+)',   # API keys
            r'token["\s]*[:=]["\s]*([^"\s,}]+)',     # tokens
            r'secret["\s]*[:=]["\s]*([^"\s,}]+)',    # secrets
        ]
    
    masked_text = text
    for pattern in patterns:
        masked_text = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), '*' * len(m.group(1))), 
                           masked_text, flags=re.IGNORECASE)
    
    return masked_text


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def retry_with_backoff(func, max_retries: int = 3, backoff_factor: float = 1.0, 
                      exceptions: tuple = (Exception,)):
    """Decorator for retrying function calls with exponential backoff"""
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    
    return decorator


class HealthChecker:
    """Simple health checker for system components"""
    
    def __init__(self):
        self.checks = {}
    
    def add_check(self, name: str, check_func: callable):
        """Add a health check function"""
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks"""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "result": result,
                    "timestamp": iso_timestamp()
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": extract_error_message(e),
                    "timestamp": iso_timestamp()
                }
        
        return results
    
    def get_overall_health(self) -> bool:
        """Get overall system health status"""
        results = self.run_checks()
        return all(check["status"] == "healthy" for check in results.values())


# Global health checker instance
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get global health checker instance"""
    return _health_checker


# Legacy function
def timestamp():
    """Legacy timestamp function"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")