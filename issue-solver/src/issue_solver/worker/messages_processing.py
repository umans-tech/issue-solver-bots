import json
import logging
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
    PullRequestCreated,
    CodingAgentRequested,
    CodingAgentImplementationStarted,
    CodingAgentImplementationCompleted,
    CodingAgentImplementationFailed,
    RepositoryIndexationRequested,
    most_recent_event,
)
from issue_solver.git_operations.git_helper import (
    GitHelper,
    GitSettings,
    GitValidationError,
)
from issue_solver.webapi.dependencies import (
    get_clock,
    get_validation_service,
    init_event_store,
)
from issue_solver.worker.vector_store_helper import (
    get_obsolete_files_ids,
    index_new_files,
    unindex_obsolete_files,
    upload_repository_files_to_vector_store,
)
from openai import OpenAI
from github import Github
from gitlab import Gitlab

logger = logging.getLogger()


async def process_event_message(message: AnyDomainEvent) -> None:
    """
    Process a repository connection message.

    Args:
        message: The SQS message containing repository information
    """
    try:
        match message:
            case CodeRepositoryConnected():
                await index_codebase(message)
            case CodeRepositoryIndexed():
                logger.info("Skipping already processed repository")
            case RepositoryIndexationRequested():
                await index_new_changes_codebase(message)
            case CodingAgentRequested():
                await dispatch_coding_agent(message)
            case PullRequestCreated():
                logger.info("Skipping already processed pull request")
    except Exception as e:
        logger.error(f"Error processing repository message: {str(e)}")
        raise


async def index_codebase(message: CodeRepositoryConnected) -> None:
    # Extract message data
    url = message.url
    access_token = message.access_token
    user_id = message.user_id
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository: {url} for user: {user_id}, process: {process_id}"
    )
    to_path = Path(f"/tmp/repo/{process_id}")

    try:
        # Use the validation service from dependencies
        git_helper = GitHelper.of(
            GitSettings(repository_url=url, access_token=access_token),
            validation_service=get_validation_service(),
        )
        code_version = git_helper.clone_repository(to_path)
        logger.info(f"Successfully cloned repository: {url}")

        # Upload repository files to vector store if knowledge_base_id is provided
        if knowledge_base_id:
            logger.info(
                f"Uploading repository files to vector store: {knowledge_base_id}"
            )
            client = OpenAI()
            stats = upload_repository_files_to_vector_store(
                repo_path=to_path, vector_store_id=knowledge_base_id, client=client
            )
            logger.info(f"Vector store upload stats: {json.dumps(stats)}")
            event_store = await init_event_store()
            await event_store.append(
                process_id,
                CodeRepositoryIndexed(
                    branch=code_version.branch,
                    commit_sha=code_version.commit_sha,
                    stats=stats,
                    knowledge_base_id=knowledge_base_id,
                    process_id=process_id,
                    occurred_at=get_clock().now(),
                ),
            )
        else:
            logger.warning(
                "No knowledge_base_id provided, skipping vector store upload"
            )
        logger.info(f"Successfully processed repository: {url}")

    except GitValidationError as e:
        logger.error(f"Git validation error: {e.message}")

        # Record the failure event
        event_store = await init_event_store()
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type=e.error_type,
                error_message=e.message,
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )

    except Exception as e:
        logger.error(f"Unexpected error processing repository: {str(e)}")

        # Record the failure event with a generic error
        event_store = await init_event_store()
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type="unexpected_error",
                error_message=f"An unexpected error occurred: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )


async def index_new_changes_codebase(message: RepositoryIndexationRequested) -> None:
    # Extract message data
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository indexation for process: {process_id}, knowledge_base_id: {knowledge_base_id}"
    )
    event_store = await init_event_store()
    events = await event_store.get(process_id)
    last_indexed_event = most_recent_event(events, CodeRepositoryIndexed)
    code_repository_connected = most_recent_event(events, CodeRepositoryConnected)
    if last_indexed_event is None or code_repository_connected is None:
        logger.warning("Missing events for process, skipping indexation")
        return
    last_indexed_commit_sha = last_indexed_event.commit_sha
    access_token = code_repository_connected.access_token
    url = code_repository_connected.url

    try:
        # Use the validation service from dependencies
        git_helper = GitHelper.of(
            GitSettings(repository_url=url, access_token=access_token),
            validation_service=get_validation_service(),
        )
        to_path = Path(f"/tmp/repo/{process_id}")
        if not to_path.exists():
            logger.info("Cloning repository")
            code_version = git_helper.clone_repository(to_path, depth=None)
        else:
            logger.info("Pulling repository")
            code_version = git_helper.pull_repository(to_path)

        files_to_index = git_helper.get_changed_files_commit(
            to_path, last_indexed_commit_sha
        )

        if not files_to_index:
            logger.info("No new commits found, skipping indexation")
            return
        logger.info(f"Indexing commit: {last_indexed_commit_sha}")
        logger.info(f"Indexing files: {files_to_index}")

        client = OpenAI()

        obsolete_files = get_obsolete_files_ids(
            files_to_index.get_paths_of_all_obsolete_files(),
            client,
            knowledge_base_id,
        )
        logger.info(f"Obsolete files stats: {json.dumps(obsolete_files.stats)}")

        new_indexed_files_stats = index_new_files(
            files_to_index.get_paths_of_all_new_files(), client, knowledge_base_id
        )
        logger.info(f"Vector store upload stats: {json.dumps(new_indexed_files_stats)}")

        unindexed_files_stats = unindex_obsolete_files(
            obsolete_files.file_ids_path, client, knowledge_base_id
        )
        logger.info(f"Unindexed files stats: {json.dumps(unindexed_files_stats)}")

        # Store the updated repository indexation event
        await event_store.append(
            process_id,
            CodeRepositoryIndexed(
                branch=code_version.branch,
                commit_sha=code_version.commit_sha,
                stats={
                    "new_indexed_files": new_indexed_files_stats,
                    "obsolete_files": obsolete_files.stats,
                    "unindexed_files": unindexed_files_stats,
                },
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
        logger.info(f"Successfully reindexed repository: {url}")

    except GitValidationError as e:
        logger.error(f"Git validation error: {e.message}")

        # Use the error information from the GitValidationError
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type=e.error_type,
                error_message=e.message,
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )

    except Exception as e:
        logger.error(f"Unexpected error during reindexing: {str(e)}")

        # Record the failure event with a generic error
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type="unexpected_error",
                error_message=f"An unexpected error occurred during reindexing: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )


async def dispatch_coding_agent(message: CodingAgentRequested) -> None:
    # Extract message data
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing coding agent for process: {process_id}, knowledge_base_id: {knowledge_base_id}"
    )
    event_store = await init_event_store()
    events = await event_store.get(process_id)
    code_repository_connected = most_recent_event(events, CodeRepositoryConnected)
    if code_repository_connected is None:
        logger.warning("Missing events for process, skipping indexation")
        return
    access_token = code_repository_connected.access_token
    url = code_repository_connected.url
    task_description = message.task_description
    branch_name = message.branch_name
    pr_title = message.pr_title

    try:
        git_settings = GitSettings(repository_url=url, access_token=access_token)
        # Use the validation service from dependencies
        git_helper = GitHelper.of(
            git_settings,
            validation_service=get_validation_service(),
        )

        to_path = Path(f"/tmp/repo/{process_id}")
        if not to_path.exists():
            logger.info("Cloning repository")
            code_version = git_helper.clone_repository(to_path, depth=None)
        else:
            logger.info("Pulling repository")
            code_version = git_helper.pull_repository(to_path)

        # Run the coding agent
        await event_store.append(
            process_id,
            CodingAgentImplementationStarted(
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
        
        run_coding_agent(task_description, to_path)

        # Record the completion event
        await event_store.append(
            process_id,
            CodingAgentImplementationCompleted(
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
        
        logger.info(f"Successfully dispatched coding agent for process: {process_id}")

        commit_changes(git_settings, to_path, branch_name, pr_title, task_description)

        pr_url = create_pull_request(git_settings, to_path, branch_name, pr_title, task_description)

        await event_store.append(
            process_id,
            PullRequestCreated(
                process_id=process_id,
                occurred_at=get_clock().now(),
                pr_url=pr_url,
                pr_title=pr_title,
                pr_description=task_description,
                knowledge_base_id=knowledge_base_id,
            ),
        )

        logger.info(f"Successfully created pull request: {pr_url}")

    except Exception as e:
        logger.error(f"Unexpected error during dispatching coding agent: {str(e)}")

        # Record the failure event with a generic error
        await event_store.append(
            process_id,
            CodingAgentImplementationFailed(
                process_id=process_id,
                occurred_at=get_clock().now(),
                error_type="unexpected_error",
                error_message=f"An unexpected error occurred during dispatching coding agent: {str(e)}",
                knowledge_base_id=knowledge_base_id,
            ),
        )


def run_coding_agent(task_description: str, to_path: Path) -> None:
    logger.info(f"Running coding agent with task: {task_description}")    
    os.chdir(to_path)
    try:
        subprocess.run(["claude", 
                        "-p", task_description,
                        "--output-format", "stream-json",
                        "--dangerously-skip-permissions"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
    except subprocess.CalledProcessError as e:
        logger.error(f"Coding agent failed with error: {e}")
        raise


def create_pull_request(git_settings: GitSettings, to_path: Path, branch_name: str, pr_title: str, task_description: str) -> None:
    logger.info(f"Creating pull request with title: {pr_title}")
    repo_type = get_repo_type(git_settings.repository_url)
    if repo_type == "github":
        create_github_pull_request(git_settings, to_path, branch_name, pr_title, task_description)
    elif repo_type == "gitlab":
        create_gitlab_pull_request(git_settings, to_path, branch_name, pr_title, task_description)
    else:
        raise ValueError(f"Unsupported repository type: {repo_type}")


def commit_changes(git_settings: GitSettings, to_path: Path, branch_name: str, pr_title: str, task_description: str) -> None:
    pass


def get_repo_type(url: str) -> str:
    if "github" in url:
        return "github"
    elif "gitlab" in url:
        return "gitlab"
    else:
        raise ValueError(f"Unsupported repository type: {url}")
    

def create_github_pull_request(git_settings: GitSettings, to_path: Path, branch_name: str, pr_title: str, task_description: str) -> str:
    logger.info(f"Creating pull request with title: {pr_title}")
    gh = Github(git_settings.access_token)
    repo = gh.get_repo(git_settings.repository_url)
    pr = repo.create_pull_request(base="main", head=branch_name, title=pr_title, body=task_description)
    logger.info(f"Pull request created: {pr.html_url}")
    return pr.html_url


def create_gitlab_pull_request(git_settings: GitSettings, to_path: Path, branch_name: str, pr_title: str, task_description: str) -> str:
    logger.info(f"Creating pull request with title: {pr_title}")
    parsed_url = urlparse(git_settings.repository_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    project_path = parsed_url.path.lstrip("/").removesuffix(".git")

    gl = Gitlab(base_url, private_token=git_settings.access_token)
    mr = gl.projects.get(project_path).mergerequests.create({
        "title": pr_title,
        "source_branch": branch_name,
        "target_branch": "main",
        "description": task_description
    })
    logger.info(f"Pull request created: {mr.web_url}")
    return mr.web_url
