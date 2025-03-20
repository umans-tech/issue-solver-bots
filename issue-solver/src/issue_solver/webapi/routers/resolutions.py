import json
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from issue_solver.agents.resolution_approaches import resolution_approach_prompt
from issue_solver.webapi.dependencies import get_agent, get_logger
from issue_solver.webapi.payloads import (
    IterateIssueResolutionRequest,
    SolveIssueRequest,
)

router = APIRouter(prefix="/resolutions", tags=["resolutions"])


@router.post("/iterate")
async def iterate_issue_resolution(
    request: IterateIssueResolutionRequest,
    logger: Annotated[
        logging.Logger,
        Depends(lambda: get_logger("issue_solver.webapi.routers.resolutions.iterate")),
    ],
):
    """Perform one iteration of issue resolution."""

    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings

    logger.info(
        f"Starting issue resolution iteration for repository at {repo_location}"
    )

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
        logger.info(
            f"Completed issue resolution iteration successfully using {settings.agent}"
        )
    except Exception as e:
        logger.error(f"Error during issue resolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return response


@router.post("/complete")
async def complete_issue_resolution(
    request: SolveIssueRequest,
    logger: Annotated[
        logging.Logger,
        Depends(lambda: get_logger("issue_solver.webapi.routers.resolutions.complete")),
    ],
):
    """Continue resolving until the issue is complete or max iterations are reached."""
    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings
    max_iter = request.max_iter

    logger.info(
        f"Starting complete issue resolution for repository at {repo_location} with max {max_iter} iterations"
    )

    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )
    messages = settings.history or []
    try:
        for i in range(max_iter):
            logger.info(f"Starting iteration {i+1}/{max_iter}")
            agent = get_agent(settings)
            response = await agent.run_full_turn(
                system_message=system_message, messages=messages, model=settings.model
            )
            messages = response.messages_history()
            if response.has_finished():
                logger.info("Issue resolution completed successfully")
                return {"status": "complete", "response": messages}

        logger.info(f"Reached maximum iterations ({max_iter}) without completion")
        return {"status": "incomplete", "messages": messages}
    except Exception as e:
        logger.error(f"Error during complete issue resolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_issue_resolution(
    request: SolveIssueRequest,
    logger: Annotated[
        logging.Logger,
        Depends(lambda: get_logger("issue_solver.webapi.routers.resolutions.stream")),
    ],
):
    """Stream issue resolution progress."""
    repo_location = request.repo_location
    issue_description = request.issue_description
    settings = request.settings
    max_iter = request.max_iter

    logger.info(
        f"Setting up streaming issue resolution for repository at {repo_location}"
    )

    system_message = resolution_approach_prompt(
        location=repo_location, pr_description=issue_description
    )

    async def stream():
        messages = settings.history or []
        try:
            for i in range(max_iter):
                logger.info(f"Starting streaming iteration {i+1}/{max_iter}")
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
                    logger.info("Issue resolution completed during streaming")
                    break

        except Exception as e:
            logger.error(f"Error during streaming issue resolution: {str(e)}")
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(stream(), media_type="application/json")
