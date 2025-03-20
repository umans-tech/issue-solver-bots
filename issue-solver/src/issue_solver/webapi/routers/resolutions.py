import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from issue_solver.agents.resolution_approaches import resolution_approach_prompt
from issue_solver.webapi.dependencies import get_agent
from issue_solver.webapi.payloads import (
    IterateIssueResolutionRequest,
    SolveIssueRequest,
)

# Get logger for your module
logger = logging.getLogger("issue_solver.webapi.routers.resolutions")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/resolutions", tags=["resolutions"])


@router.post("/iterate")
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


@router.post("/complete")
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


@router.post("/stream")
async def stream_issue_resolution(request: SolveIssueRequest):
    """Stream issue resolution progress."""
    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings
    max_iter = request.max_iter
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