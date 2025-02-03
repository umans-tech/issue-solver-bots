import inspect

from openai.types.shared_params import FunctionDefinition


def bash_tool_schema() -> FunctionDefinition:
    """Creates JSON schema for bash tool compatible with OpenAI functions."""
    return FunctionDefinition(
        name="bash",
        description="Executes bash commands to inspect and modify files in the repository.",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute.",
                }
            },
            "required": ["command"],
        },
    )


def edit_tool_schema() -> FunctionDefinition:
    """Creates JSON schema for edit tool compatible with OpenAI functions."""
    return FunctionDefinition(
        name="str_replace_editor",
        description="Allows the agent to view, edit, and manipulate files in the repository.",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": [
                        "view",
                        "create",
                        "str_replace",
                        "insert",
                        "undo_edit",
                    ],
                    "description": "The editing command to execute. Options: 'view', 'create', 'str_replace', 'insert', 'undo_edit'.",
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
        },
    )


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


def bash_description() -> str:
    return """
            Run commands in a bash shell\n
            * When invoking this tool, the contents of the \"command\" parameter does NOT need to be XML-escaped.\n
            * You don't have access to the internet via this tool.\n
            * You do have access to a mirror of common linux and python packages via apt and pip.\n
            * State is persistent across command calls and discussions with the user.\n
            * To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.\n
            * Please avoid commands that may produce a very large amount of output.\n
            * Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.
    """


def bash_tool() -> dict:
    return {
        "name": "bash",
        "description": bash_description(),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run.",
                }
            },
            "required": ["command"],
        },
    }


def edit_description() -> str:
    return """
        Custom tools for viewing, creating and editing files\n
        * State is persistent across command calls and discussions with the user\n
        * If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n
        * The `create` cannot be used if `path` already exists as a file\n
        * Long outputs are truncated and marked with `<response clipped>` \n
        * `undo_edit` reverts the last edit made to the file at `path`\n
        \n
        `str_replace` command:\n
        * The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n
        * If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n
        * The `new_str` parameter should contain the edited lines that should replace the `old_str`
    """


def edit_tool() -> dict:
    return {
        "name": "str_replace_editor",
        "description": edit_description(),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                    "description": "The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.",
                },
                "file_text": {
                    "description": "Required parameter of `create` command, with the content of the file to be created.",
                    "type": "string",
                },
                "insert_line": {
                    "description": "Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.",
                    "type": "integer",
                },
                "new_str": {
                    "description": "Required parameter of `str_replace` command containing the new string. Required parameter of `insert` command containing the string to insert.",
                    "type": "string",
                },
                "old_str": {
                    "description": "Required parameter of `str_replace` command containing the string in `path` to replace.",
                    "type": "string",
                },
                "path": {
                    "description": "Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.",
                    "type": "string",
                },
                "view_range": {
                    "description": "Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
                    "items": {"type": "integer"},
                    "type": "array",
                },
            },
            "required": ["command", "path"],
        },
    }
