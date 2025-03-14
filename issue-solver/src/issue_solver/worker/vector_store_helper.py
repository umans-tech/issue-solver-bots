"""
Helper module for vector store operations.
"""

import concurrent.futures
import logging
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)


# File extensions that we support
SUPPORTED_EXTENSIONS = {
    ".c",
    ".cpp",
    ".cs",
    ".css",
    ".doc",
    ".docx",
    ".go",
    ".html",
    ".java",
    ".js",
    ".json",
    ".md",
    ".pdf",
    ".php",
    ".pptx",
    ".py",
    ".rb",
    ".sh",
    ".tex",
    ".ts",
    ".txt",
}


# Maximum file size in bytes (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def is_valid_code_file(file_path: str) -> bool:
    """
    Check if a file is a valid code file to be uploaded.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if the file is valid, False otherwise
    """
    # Check file extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        return False

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

    # Check if file is binary
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read(1024)  # Try to read the first 1024 bytes
        return True
    except UnicodeDecodeError:
        # File is likely binary
        return False


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
    try:
        if not is_valid_code_file(file_path):
            return {
                "file": file_name,
                "status": "skipped",
                "reason": "Invalid file type or binary file",
            }

        logger.info(f"Uploading file: {file_name}")
        file_response = client.files.create(
            file=open(file_path, "rb"), purpose="assistants"
        )
        # Store the response but don't assign to a variable since we don't use it
        client.vector_stores.files.create(
            vector_store_id=vector_store_id, file_id=file_response.id
        )
        return {"file": file_name, "status": "success"}
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

    stats: dict[str, Any] = {
        "total_files": len(all_files),
        "successful_uploads": 0,
        "failed_uploads": 0,
        "skipped_files": 0,
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
                stats["skipped_files"] += 1

    logger.info(
        f"Upload complete. {stats['successful_uploads']} files uploaded successfully, "
        f"{stats['failed_uploads']} failed, {stats['skipped_files']} skipped."
    )

    return stats
