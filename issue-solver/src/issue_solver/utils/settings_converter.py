"""Utility functions for converting BaseSettings objects to .env file format."""

from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


def settings_to_env_string(settings: BaseSettings) -> str:
    """
    Convert a BaseSettings object to .env file content string.
    
    Args:
        settings: The BaseSettings object to convert
        
    Returns:
        A string containing the equivalent .env file content
        
    Features:
    - Handles nested BaseSettings objects using env_nested_delimiter (default '__')
    - Handles env_prefix from model_config
    - Formats values appropriately (strings with spaces in quotes, booleans as lowercase)
    - Sorts keys for consistent output
    - Skips None values
    """
    env_vars = _extract_env_variables(settings)
    
    if not env_vars:
        return ""
    
    # Sort keys for consistent output
    sorted_vars = sorted(env_vars.items())
    
    # Format each variable
    lines = []
    for key, value in sorted_vars:
        formatted_value = _format_env_value(value)
        lines.append(f"{key}={formatted_value}")
    
    return "\n".join(lines)


def _extract_env_variables(settings: BaseSettings, parent_prefix: str = "") -> Dict[str, Any]:
    """
    Extract environment variables from a BaseSettings object.
    
    Args:
        settings: The BaseSettings object to extract from
        parent_prefix: Prefix to prepend to variable names (for nested objects)
        
    Returns:
        Dictionary of environment variable names to their values
    """
    env_vars = {}
    
    # Get configuration from model_config
    model_config = getattr(settings, 'model_config', None)
    env_prefix = ""
    env_nested_delimiter = "__"
    
    if model_config:
        env_prefix = getattr(model_config, 'env_prefix', "")
        env_nested_delimiter = getattr(model_config, 'env_nested_delimiter', "__")
    
    # Determine the current prefix for this level
    current_prefix = ""
    if parent_prefix:
        # We're in a nested context, use parent prefix
        current_prefix = parent_prefix
    elif env_prefix:
        # We're at root level with an env_prefix
        current_prefix = env_prefix.rstrip('_')
    
    # Get all field values
    for field_name, field_info in settings.model_fields.items():
        value = getattr(settings, field_name)
        
        # Skip None values
        if value is None:
            continue
            
        field_name_upper = field_name.upper()
        
        # Handle nested BaseSettings objects
        if isinstance(value, BaseSettings):
            # Build nested prefix using delimiter
            if current_prefix:
                nested_prefix = f"{current_prefix}{env_nested_delimiter}{field_name_upper}"
            else:
                nested_prefix = field_name_upper
            nested_vars = _extract_env_variables(value, nested_prefix)
            env_vars.update(nested_vars)
        else:
            # Build the environment variable name for non-nested values
            if current_prefix:
                # Use the appropriate delimiter based on context
                if parent_prefix:
                    # We're in a nested object - use the nested delimiter but only once more
                    env_var_name = f"{current_prefix}{env_nested_delimiter}{field_name_upper}"
                else:
                    # We're at root level with prefix - use underscore
                    if current_prefix.endswith('_'):
                        env_var_name = f"{current_prefix}{field_name_upper}"
                    else:
                        env_var_name = f"{current_prefix}_{field_name_upper}"
            else:
                env_var_name = field_name_upper
            env_vars[env_var_name] = value
    
    return env_vars


def _format_env_value(value: Any) -> str:
    """
    Format a value for use in a .env file.
    
    Args:
        value: The value to format
        
    Returns:
        Formatted string representation suitable for .env files
    """
    if value is None:
        return ""
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, Path):
        path_str = str(value)
        # Quote paths that contain spaces
        if " " in path_str:
            return f'"{path_str}"'
        return path_str
    elif isinstance(value, AnyUrl):
        url_str = str(value)
        # Quote URLs that contain spaces (unlikely but possible)
        if " " in url_str:
            return f'"{url_str}"'
        return url_str
    elif isinstance(value, str):
        # Quote strings that contain spaces or quotes
        if " " in value or '"' in value:
            # Escape any existing quotes
            escaped_value = value.replace('"', '\\"')
            return f'"{escaped_value}"'
        return value
    else:
        # For any other type, convert to string and apply string rules
        str_value = str(value)
        if " " in str_value or '"' in str_value:
            escaped_value = str_value.replace('"', '\\"')
            return f'"{escaped_value}"'
        return str_value