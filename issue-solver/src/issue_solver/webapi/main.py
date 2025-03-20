import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import assert_never, Annotated

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from openai import OpenAI
from starlette.requests import Request

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

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Get logger for your module
logger = logging.getLogger("issue_solver.webapi")
logger.setLevel(logging.INFO)

# Make sure it propagates up to root logger
logger.propagate = True


class InMemoryEventStore:
    def __init__(self):
        self.events = {}

    def append(self, process_id, event):
        if process_id not in self.events:
            self.events[process_id] = []
        self.events[process_id].append(event)

    def get(self, process_id):
        return self.events.get(process_id, [])


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    fastapi_app.state.event_store = InMemoryEventStore()
    yield
    del fastapi_app.state.event_store


app = FastAPI(lifespan=lifespan)


def get_event_store(request: Request) -> InMemoryEventStore:
    return request.app.state.event_store


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


@dataclass(frozen=True)
class CodeRepositoryConnected:
    url: str
    access_token: str
    user_id: str
    knowledge_base_id: str
    process_id: str


@app.post("/repositories/", status_code=201)
def connect_repository(
    connect_repository_request: ConnectRepositoryRequest,
    event_store: Annotated[InMemoryEventStore, Depends(get_event_store)],
):
    process_id = str(uuid.uuid4())
    client = OpenAI()
    repo_name = connect_repository_request.url.split("/")[-1]
    vector_store = client.vector_stores.create(name=repo_name)
    event = CodeRepositoryConnected(
        url=connect_repository_request.url,
        access_token=connect_repository_request.access_token,
        user_id="Todo: get user id",
        knowledge_base_id=vector_store.id,
        process_id=process_id,
    )
    event_store.append(process_id, event)
    publish(event)
    return {
        "url": event.url,
        "process_id": event.process_id,
        "knowledge_base_id": event.knowledge_base_id,
    }


@app.get("/processes/{process_id}")
def get_process(
    process_id: str,
    event_store: Annotated[InMemoryEventStore, Depends(get_event_store)],
):
    process_events = event_store.get(process_id)
    if not process_events:
        raise HTTPException(status_code=404, detail="Process not found")

    return {"process_id": process_id}


def publish(event: CodeRepositoryConnected) -> None:
    try:
        logger.info(f"Publishing {event.process_id}")
        sqs_client = boto3.client(
            "sqs", region_name=os.environ.get("AWS_REGION", "eu-west-3")
        )

        queue_url = os.environ.get("PROCESS_QUEUE_URL")
        if not queue_url:
            raise ValueError("PROCESS_QUEUE_URL environment variable not set")

        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(
                {
                    "url": event.url,
                    "access_token": event.access_token,
                    "user_id": event.user_id,
                    "process_id": event.process_id,
                    "knowledge_base_id": event.knowledge_base_id,
                }
            ),
        )

        logger.info(
            f"Published {event.process_id} successfully with message id {response['MessageId']}"
        )

    except (ClientError, ValueError) as e:
        logger.error(f"Failed to publish {event.process_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send message to SQS: {str(e)}"
        )


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
