import os
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from issue_solver.agents.openai_with_tools.openai_agent import OpenAIAgent
from issue_solver.agents.openai_with_tools.setup import resolution_approach_prompt

app = FastAPI()

open_ai_agent = OpenAIAgent(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini")


@app.post("/resolutions")
async def solve_issue_move_next(repo_location: str, issue_description: str,
                                messages: Optional[List[ChatCompletionMessageParam]] = None):
    system_message = resolution_approach_prompt(location=repo_location, pr_description=issue_description)
    one_turn_messages = await open_ai_agent.run_full_turn(system_message=system_message, messages=messages or [])
    return one_turn_messages


@app.post("/resolutions/iterate")
async def iterate_issue_resolution(repo_location: str, issue_description: str,
                                   messages: Optional[List[ChatCompletionMessageParam]] = None):
    """Perform one iteration of issue resolution."""
    system_message = resolution_approach_prompt(location=repo_location, pr_description=issue_description)
    try:
        response = await open_ai_agent.run_full_turn(system_message=system_message, messages=messages or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response


@app.post("/resolutions/complete")
async def complete_issue_resolution(repo_location: str, issue_description: str,
                                    max_iter: int = 10):
    """Continue resolving until the issue is complete or max iterations are reached."""
    system_message = resolution_approach_prompt(location=repo_location, pr_description=issue_description)
    messages = []
    try:
        for _ in range(max_iter):
            response = await open_ai_agent.run_full_turn(system_message=system_message, messages=messages)
            if "stop_reason" in response and response["stop_reason"] == "stop":
                return {"status": "complete", "response": response}
        return {"status": "incomplete", "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
