from anthropic.types import ToolParam


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


def bash_tool() -> ToolParam:
    return ToolParam(
        name="bash",
        description=bash_description(),
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run.",
                }
            },
            "required": ["command"],
        },
    )


def edit_description() -> str:
    return """
        Custom editing tool for viewing, creating and editing files\n
        * State is persistent across command calls and discussions with the user\n
        * If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n
        * The `create` command cannot be used if the specified `path` already exists as a file\n
        * If a `command` generates a long output, it will be truncated and marked with `<response clipped>` \n
        * The `undo_edit` command will revert the last edit made to the file at `path`\n
        \n
        Notes for using the `str_replace` command:\n
        * The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n
        * If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n
        * The `new_str` parameter should contain the edited lines that should replace the `old_str`
    """


def edit_tool() -> ToolParam:
    return ToolParam(
        name="str_replace_editor",
        description=edit_description(),
        input_schema={
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
    )
