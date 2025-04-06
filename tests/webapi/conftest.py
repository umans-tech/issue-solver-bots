import asyncio
import os
import time
from datetime import datetime
from typing import Any, Generator

import asyncpg
import boto3
import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from issue_solver.git_operations.git_helper import NoopGitValidationService
from issue_solver.webapi.dependencies import get_clock, get_validation_service
from issue_solver.webapi.main import app
from pytest_httpserver import HTTPServer
from starlette.testclient import TestClient
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from tests.controllable_clock import ControllableClock
from tests.fixtures import ALEMBIC_INI_LOCATION, MIGRATIONS_PATH

# Test configuration constants
CREATED_VECTOR_STORE_ID = "vs_abc123"
DEFAULT_CURRENT_TIME = datetime.fromisoformat("2022-01-01T00:00:00")


# Create a function to get a NoopGitValidationService for tests
def get_test_validation_service():
    """Returns a NoopGitValidationService for tests.
    
    This service doesn't perform actual Git validation and always succeeds,
    allowing tests to run without real Git repositories or network connections.
    
    By using dependency injection rather than environment variables,
    we ensure a more reliable and explicit testing environment.
    """
    return NoopGitValidationService() 