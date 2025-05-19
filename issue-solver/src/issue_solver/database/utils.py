"""Utility functions for database connections."""
from itertools import count
from typing import Any, Callable, Dict, Optional

# Counter for generating unique prepared statement names
_stmt_counter = count()


def get_pgbouncer_safe_connect_args(
    statement_name_prefix: str = "ps"
) -> Dict[str, Any]:
    """
    Return connection arguments for pgbouncer compatibility.
    
    This prevents the 'prepared statement "ps_xx" already exists' error
    when using pgbouncer in transaction pooling mode.
    
    Args:
        statement_name_prefix: Prefix to use for prepared statements
    
    Returns:
        Dictionary with connection arguments
    """
    return {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda operation=None: f"{statement_name_prefix}_{next(_stmt_counter)}",
        "server_settings": {
            "statement_timeout": "10000",  # 10 seconds
            "idle_in_transaction_session_timeout": "60000",  # 60 seconds
        },
    }


def get_sqlalchemy_connect_args() -> Dict[str, Any]:
    """
    Return connection arguments for SQLAlchemy engines.
    
    This is a wrapper around get_pgbouncer_safe_connect_args,
    with any SQLAlchemy-specific settings.
    
    Returns:
        Dictionary with connection arguments for SQLAlchemy
    """
    return get_pgbouncer_safe_connect_args()