from typing import Any, cast
import json

from openai import OpenAI

from issue_solver.agents.openai_with_tools.tools import bash_tool, edit_tool
from issue_solver.agents.openai_with_tools.tools.base import ToolResult
from issue_solver.agents.openai_with_tools.tools.bash import BashTool
from issue_solver.agents.openai_with_tools.tools.edit import EditTool

MODEL_NAME = "gpt-4o-mini"
MAX_ITER = 20

def resolution_approach_prompt(location: str, pr_description: str) -> str:
    return f"""
        <uploaded_files>
        {location}
        </uploaded_files>
        I've uploaded a python code repository in the directory {location} (not in /tmp/inputs). Consider the following PR description:
        
        <pr_description>
        {pr_description}
        </pr_description>
        
        Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?
        I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!
        
        Your task is to make the minimal changes to non-tests files in the {location} directory to ensure the <pr_description> is satisfied.
        
        Follow these steps to resolve the issue:
        1. As a first step, it might be a good idea to explore the repo to familiarize yourself with its structure.
        2. Create a script to reproduce the error and execute it with `python <filename.py>` using the BashTool, to confirm the error
        3. Edit the sourcecode of the repo to resolve the issue
        4. Rerun your reproduce script and confirm that the error is fixed!
        5. Think about edgecases and make sure your fix handles them as well
        
        Your thinking should be thorough and so it's fine if it's very long.
    """


async def start_resolution():
    print("Starting resolution")
    client = OpenAI()

    messages_history = [{
        "role": "user",
        "content": resolution_approach_prompt(
            location="/Users/naji/Documents/Projects/tutor/swe-agent/issue-solver-bots/issue-solver",
            pr_description="Fix the rounding issue in the marshmallow library at /src/marshmallow/fields.py#L1474"
        )
    }]
    tools_list = [
        {
        "type": "function",
        "function": bash_tool()
        },
        {
        "type": "function",
        "function": edit_tool()
        },
    ]

    nb_iter = 1
    
    while True:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            tools=tools_list,
            messages=messages_history,
        )

        messages_history.append(response.choices[0].message)
        tool_calls = response.choices[0].message.tool_calls

        if tool_calls:
            tool_call = tool_calls[0]
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)
            tool_id = tool_call.id

            print(f"\nTool Used: {tool_name}")
            print(f"Tool Input: {tool_input}")


            tool_result = await process_tool_call(tool_name, tool_input)

            tool_result_content = _make_api_tool_result(await tool_result, tool_call.id)

            messages_history.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": str(tool_result_content),
            })

            print(messages_history)
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_history,
                tools=tools_list,
            )

            nb_iter += 1
            if nb_iter > MAX_ITER:
                break
        else:
            break
        

    final_response = response.choices[0].message.content
    
    print(f"\nFinal Response: {final_response}")

    print(response)


def _make_api_tool_result(
        result: ToolResult, tool_use_id: str
):
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text


async def process_tool_call(tool_name, tool_input):
    if tool_name == "str_replace_editor":
        return EditTool()(**tool_input)
    elif tool_name == "bash":
        return BashTool()(**tool_input)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def pr_description():
    return """
        Hi there!

        I just found quite strange behaviour of TimeDelta field serialization
        
        ```python
        from marshmallow.fields import TimeDelta
        from datetime import timedelta
        
        td_field = TimeDelta(precision="milliseconds")
        
        obj = dict()
        obj["td_field"] = timedelta(milliseconds=345)
        
        print(td_field.serialize("td_field", obj))
        ```
        Output of this snippet is 344, but it seems that 345 is correct.
        
        Looks like a rounding issue here: https://github.com/marshmallow-code/marshmallow/blob/dev/src/marshmallow/fields.py#L1474
    """
