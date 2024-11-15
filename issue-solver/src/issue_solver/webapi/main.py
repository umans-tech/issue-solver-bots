import os
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from issue_solver import AgentModel
from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.agents.coding_agent import CodingAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.agents.resolution_approaches import resolution_approach_prompt

app = FastAPI()

open_ai_agent = OpenAIAgent(
    api_key=os.environ["OPENAI_API_KEY"], default_model=AgentModel.GPT4O_MINI
)

claude_agent = AnthropicAgent(
    api_key=os.environ["ANTHROPIC_API_KEY"], default_model=AgentModel.CLAUDE_35_HAIKU
)


@app.post("/resolutions/iterate")
async def iterate_issue_resolution(
        repo_location: str,
        issue_description: str,
        model: AgentModel = AgentModel.GPT4O_MINI,
        messages: Optional[List[ChatCompletionMessageParam]] = None,
):
    """Perform one iteration of issue resolution."""
    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )
    try:
        agent = get_agent(model)
        response = await agent.run_full_turn(
            system_message=system_message, messages=messages or [], model=model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response


@app.post("/resolutions/complete")
async def complete_issue_resolution(
        repo_location: str,
        issue_description: str,
        model: AgentModel = AgentModel.GPT4O_MINI,
        max_iter: int = 10,
):
    """Continue resolving until the issue is complete or max iterations are reached."""
    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )
    messages = []
    try:
        for _ in range(max_iter):
            agent = get_agent(model)
            response = await agent.run_full_turn(
                system_message=system_message, messages=messages, model=model
            )
            messages = response.messages_history()
            if response.has_finished():
                return {"status": "complete", "response": response}
        return {"status": "incomplete", "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_agent(model: AgentModel) -> CodingAgent:
    if "claude" in model:
        agent = claude_agent
    elif "gpt" in model:
        agent = open_ai_agent
    else:
        raise ValueError(f"Model {model} is not supported.")
    return agent
