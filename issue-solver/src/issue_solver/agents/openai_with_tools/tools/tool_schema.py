import inspect

# issue_solver/agents/openai_with_tools/tools/tool_schema.py

from typing import Any


def bash_tool_schema() -> dict[str, Any]:
    """Creates JSON schema for bash tool compatible with OpenAI functions."""
    return {
        "name": "bash_command",
        "description": "Executes bash commands to inspect and modify files in the repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute.",
                }
            },
            "required": ["command"],
        }
    }


def edit_tool_schema() -> dict[str, Any]:
    """Creates JSON schema for edit tool compatible with OpenAI functions."""
    return {
        "name": "edit_file",
        "description": "Allows the agent to view, edit, and manipulate files in the repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                    "description": "The editing command to execute. Options: 'view', 'create', 'str_replace', 'insert', 'undo_edit'."
                },
                "file_text": {
                    "type": "string",
                    "description": "Content for 'create' command, containing the file's text.",
                },
                "insert_line": {
                    "type": "integer",
                    "description": "Required for 'insert' command, specifies the line number after which to insert new text.",
                },
                "new_str": {
                    "type": "string",
                    "description": "New content for 'str_replace' and 'insert' commands.",
                },
                "old_str": {
                    "type": "string",
                    "description": "String to replace in 'str_replace' command.",
                },
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file or directory.",
                },
                "view_range": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "For 'view' command, specifies line range, e.g., [10, 20] to view lines 10 to 20.",
                },
            },
            "required": ["command", "path"],
        }
    }


def function_to_schema(func) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
