import json
import os
from typing import assert_never

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.agents.coding_agent import CodingAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.agents.resolution_approaches import resolution_approach_prompt
from issue_solver.webapi.payloads import (
    IterateIssueResolutionRequest,
    SolveIssueRequest,
    ResolutionSettings,
    ConnectRepositoryRequest,
)

app = FastAPI()


@app.post("/resolutions/iterate")
async def iterate_issue_resolution(
    request: IterateIssueResolutionRequest,
):
    """Perform one iteration of issue resolution."""

    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings
    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )
    try:
        agent = get_agent(settings)
        response = await agent.run_full_turn(
            system_message=system_message,
            messages=settings.history or [],
            model=settings.model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response


@app.post("/resolutions/complete")
async def complete_issue_resolution(
    request: SolveIssueRequest,
):
    """Continue resolving until the issue is complete or max iterations are reached."""
    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings
    max_iter = request.max_iter
    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )
    messages = settings.history or []
    try:
        for _ in range(max_iter):
            agent = get_agent(settings)
            response = await agent.run_full_turn(
                system_message=system_message, messages=messages, model=settings.model
            )
            messages = response.messages_history()
            if response.has_finished():
                return {"status": "complete", "response": messages}
        return {"status": "incomplete", "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resolutions/stream")
async def stream_issue_resolution(request: SolveIssueRequest):
    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings
    max_iter = request.max_iter
    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )
    """Stream issue resolution progress."""
    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )

    async def stream():
        messages = settings.history or []
        try:
            for i in range(max_iter):
                agent = get_agent(settings)
                response = await agent.run_full_turn(
                    system_message=system_message,
                    messages=messages,
                    model=settings.model,
                )
                messages = response.messages_history()

                yield (
                    json.dumps(
                        {
                            "iteration": i,
                            "messages": response.turn_messages(),
                            "status": "in-progress"
                            if not response.has_finished()
                            else "finished",
                        }
                    )
                    + "\n"
                )

                if response.has_finished():
                    break

        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(stream(), media_type="application/json")


@app.post("/repositories/", status_code=201)
def connect_repository(connect_repository_request: ConnectRepositoryRequest):
    url = connect_repository_request.url
    access_token = connect_repository_request.access_token
    return {"url": url, "access_token": access_token}


def get_agent(setting: ResolutionSettings) -> CodingAgent:
    match setting.agent:
        case "openai-tools":
            return OpenAIAgent(api_key=os.environ["OPENAI_API_KEY"])
        case "anthropic-tools":
            return AnthropicAgent(
                api_key=os.environ["ANTHROPIC_API_KEY"],
            )
        case _:
            assert_never(setting.agent)
