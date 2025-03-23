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
    ".ts",
    ".txt",
    ".webp",
    ".xlsx",
    ".xml",
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


def prepare_file_path_to_upload(file_path: str, is_supported_extension: bool):
    if is_supported_extension:
        return file_path
    else:
        os.rename(file_path, file_path + ".txt")
        return file_path + ".txt"


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

        # Determine if we need to treat this as a txt file
        is_supported_extension = file_extension.lower() in SUPPORTED_EXTENSIONS

        logger.info(
            f"Uploading file: {file_name}{' as text file' if not is_supported_extension else ''}"
        )

        file_path_to_upload = prepare_file_path_to_upload(file_path, is_supported_extension)
        file_response = client.files.create(file=open(file_path_to_upload, "rb"), purpose="assistants")
        client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_response.id,
            attributes={
                "file_name": file_name,
                # file_path is prepended by /tmp/repo/{process_id}, so we extract just the relevant part
                "file_path": f"/{("/").join(file_path.split("/")[4:])}",
                "file_extension": file_extension,
            },
        )
        return {
            "file": file_name,
            "status": "success",
            "processed_as": "text" if not is_supported_extension else "native",
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
