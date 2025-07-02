"""
Helper module for vector store operations.
"""

import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from openai.types.shared_params import ComparisonFilter
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Configure logging
logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {
    ".c",
    ".cpp",
    ".css",
    ".csv",
    ".doc",
    ".docx",
    ".gif",
    ".go",
    ".html",
    ".java",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".md",
    ".pdf",
    ".php",
    ".pkl",
    ".png",
    ".pptx",
    ".py",
    ".rb",
    ".tex",
    ".tf",
    ".ts",
    ".txt",
    ".webp",
    ".xlsx",
}


# Maximum file size in bytes (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


@dataclass
class ObsoleteFilesStats:
    stats: dict[str, Any]
    file_ids_path: list[tuple[str, str]]


def is_valid_code_file(file_path: str) -> bool:
    """
    Check if a file is a valid code file to be uploaded.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if the file is valid, False otherwise
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return False

    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        return False

    # Check if file is empty
    if file_size == 0:
        return False

    # Check if file can be decoded as text
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read(1024)  # Try to read the first 1024 bytes

        # If we got here, the file is decodable as text
        # We'll accept any Unicode-decodable file, regardless of extension
        return True

    except UnicodeDecodeError:
        # File is likely binary
        return False


def prepare_file_path_to_upload(file_path: str) -> str:
    is_supported_extension = file_path.endswith(tuple(SUPPORTED_EXTENSIONS))
    if is_supported_extension:
        return file_path
    else:
        os.rename(file_path, file_path + ".txt")
        return file_path + ".txt"


def path_from_repo_root(file_path: str) -> str:
    repo_root_pattern = "/tmp/repo/{process_id}"
    position_of_repo_root = len(repo_root_pattern.split("/"))
    path_slots_from_repo_root = file_path.split("/")[position_of_repo_root:]
    return f"/{('/').join(path_slots_from_repo_root)}"


@retry(wait=wait_random_exponential(min=5, max=70), stop=stop_after_attempt(10))
def upload_file_with_retry(
    file_path, vector_store_id, client, file_name, file_extension, file_path_to_upload
):
    file_response = client.files.create(
        file=open(file_path_to_upload, "rb"), purpose="assistants"
    )
    client.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=file_response.id,
        attributes={
            "file_name": file_name,
            "file_path": path_from_repo_root(file_path),
            "file_extension": file_extension,
        },
    )


def upload_single_file(
    file_path: str, vector_store_id: str, client: OpenAI
) -> dict[str, Any]:
    """
    Upload a single file to the vector store.

    Args:
        file_path: Path to the file
        vector_store_id: ID of the vector store
        client: OpenAI client instance

    Returns:
        dict with status information
    """
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1]

    try:
        # Check if the file is valid (can be text-decoded)
        if not is_valid_code_file(file_path):
            return {
                "file": file_name,
                "status": "skipped",
                "reason": "Invalid file type or binary file",
            }

        file_path_to_upload = prepare_file_path_to_upload(file_path)

        extension_has_changed = file_path_to_upload == file_path

        logger.info(
            f"Uploading file: {file_name}{' as text file' if not extension_has_changed else ''}"
        )

        upload_file_with_retry(
            file_path,
            vector_store_id,
            client,
            file_name,
            file_extension,
            file_path_to_upload,
        )

        logger.info(f"File {file_name} uploaded successfully")
        return {
            "file": file_name,
            "status": "success",
            "processed_as": "text" if not extension_has_changed else "native",
        }
    except Exception as e:
        logger.error(f"Error with {file_name}: {str(e)}")
        return {"file": file_name, "status": "failed", "error": str(e)}


def upload_repository_files_to_vector_store(
    repo_path: Path, vector_store_id: str, client: OpenAI | None = None
) -> dict[str, Any]:
    """
    Upload all valid code files from a repository to a vector store.

    Args:
        repo_path: Path to the repository
        vector_store_id: ID of the vector store
        client: OpenAI client instance (optional)

    Returns:
        dict with statistics about the upload process
    """
    if client is None:
        client = OpenAI()

    # Get all files in the repository
    all_files = []
    for root, _, files in os.walk(repo_path):
        # Skip .git directory
        if ".git" in root.split(os.sep):
            continue

        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    stats = index_new_files(all_files, client, vector_store_id)

    return stats


def index_new_files(all_files, client, vector_store_id):
    stats: dict[str, Any] = {
        "total_files": len(all_files),
        "successful_uploads": 0,
        "failed_uploads": 0,
        "skipped_uploads": 0,
        "skipped_files": [],
        "errors": [],
    }
    logger.info(f"{len(all_files)} files found in repository. Uploading in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(
                upload_single_file, file_path, vector_store_id, client
            ): file_path
            for file_path in all_files
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result["status"] == "success":
                stats["successful_uploads"] += 1
            elif result["status"] == "failed":
                stats["failed_uploads"] += 1
                stats["errors"].append(result)
            elif result["status"] == "skipped":
                stats["skipped_uploads"] += 1
                stats["skipped_files"].append(result)
    logger.info(
        f"Upload complete. {stats['successful_uploads']} files uploaded successfully, "
        f"{stats['failed_uploads']} failed, {stats['skipped_uploads']} skipped."
    )
    return stats


@retry(wait=wait_random_exponential(min=5, max=70), stop=stop_after_attempt(10))
def search_file_id_with_retry(client, knowledge_base_id, relative_file_path):
    results = client.vector_stores.search(
        vector_store_id=knowledge_base_id,
        query=relative_file_path,
        filters=ComparisonFilter(
            type="eq",
            key="file_path",
            value=relative_file_path,
        ),
        max_num_results=1,
    )
    if len(results.data) == 0:
        return None
    file_id = results.data[0].file_id
    return file_id


def get_file_id_from_path(client, knowledge_base_id, file_path):
    relative_file_path = path_from_repo_root(file_path)

    try:
        file_id = search_file_id_with_retry(
            client, knowledge_base_id, relative_file_path
        )
        logger.info(f"File {relative_file_path} found in vector store")
        if file_id is None:
            return {
                "file": relative_file_path,
                "file_id": None,
                "status": "skipped",
                "reason": "File not found in vector store",
            }
        return {
            "file": relative_file_path,
            "file_id": file_id,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error getting file id from path {relative_file_path}: {str(e)}")
        return {
            "file": relative_file_path,
            "file_id": None,
            "status": "failed",
            "error": str(e),
        }


def get_obsolete_files_ids(
    path_of_obsolete_files: list[str], client, knowledge_base_id
) -> ObsoleteFilesStats:
    stats: dict[str, Any] = {
        "total_obsolete_files": len(path_of_obsolete_files),
        "successful_search": 0,
        "failed_search": 0,
        "errors": [],
        "skipped_files": 0,
    }
    file_ids_path = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(
                get_file_id_from_path, client, knowledge_base_id, file_path
            ): file_path
            for file_path in path_of_obsolete_files
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result["status"] == "success":
                stats["successful_search"] += 1
                file_ids_path.append((result["file_id"], result["file"]))
            elif result["status"] == "failed":
                stats["failed_search"] += 1
                stats["errors"].append(result)
            elif result["status"] == "skipped":
                stats["skipped_files"] += 1
    return ObsoleteFilesStats(stats=stats, file_ids_path=file_ids_path)


@retry(wait=wait_random_exponential(min=5, max=70), stop=stop_after_attempt(10))
def delete_single_file_from_vector_store_with_retry(client, knowledge_base_id, file_id):
    client.vector_stores.files.delete(
        vector_store_id=knowledge_base_id,
        file_id=file_id,
    )


def unindex_single_obsolete_file(client, knowledge_base_id, stats, file_id, file_path):
    try:
        delete_single_file_from_vector_store_with_retry(
            client, knowledge_base_id, file_id
        )
        logger.info(f"File {file_path} with file id {file_id} unindexed successfully")
        return {
            "file_id": file_id,
            "file_path": file_path,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error unindexing {file_path} with file id {file_id}: {str(e)}")
        return {
            "file_id": file_id,
            "file_path": file_path,
            "status": "failed",
            "error": str(e),
        }


def unindex_obsolete_files(
    file_ids_path_to_unindex: list[tuple[str, str]],
    client: OpenAI,
    knowledge_base_id: str,
) -> dict[str, Any]:
    """
    Unindex obsolete files from the vector store.

    Args:
        path_of_file_to_unindex: List of file paths to unindex
        client: OpenAI client instance
        knowledge_base_id: ID of the vector store

    Returns:
        dict with status information
    """
    stats: dict[str, Any] = {
        "total_files": len(file_ids_path_to_unindex),
        "successful_unindexing": 0,
        "failed_unindexing": 0,
        "errors": [],
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(
                unindex_single_obsolete_file,
                client,
                knowledge_base_id,
                stats,
                file_id,
                file_path,
            ): (file_id, file_path)
            for file_id, file_path in file_ids_path_to_unindex
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result["status"] == "success":
                stats["successful_unindexing"] += 1
            elif result["status"] == "failed":
                stats["failed_unindexing"] += 1
                stats["errors"].append(result)
    return stats
