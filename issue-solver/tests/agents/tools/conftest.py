import asyncio
import os
import signal
from pathlib import Path

import pytest
import pytest_asyncio

from issue_solver.agents.tools.bash import BashTool
from issue_solver.agents.tools.edit import EditTool


@pytest_asyncio.fixture
async def bash_tool():
    tool = BashTool()
    yield tool
    if tool._session and tool._session._process.returncode is None:
        await terminate_session(tool._session._process, tool._session.stop)


@pytest.fixture
def edit_tool():
    return EditTool()


@pytest.fixture
def abs_tmp_path(tmp_path: Path) -> Path:
    """Resolved tmp_path for absolute-path validations."""
    return tmp_path.resolve()


@pytest.fixture
def sample_repo(abs_tmp_path: Path) -> Path:
    """Tiny repo layout for navigation/editing stories."""
    (abs_tmp_path / "README.md").write_text("hello\n")
    (abs_tmp_path / "src").mkdir()
    (abs_tmp_path / "src" / "app.py").write_text("print('hi')\n")
    (abs_tmp_path / "docs").mkdir()
    (abs_tmp_path / "docs" / "guide.md").write_text("usage\n")
    return abs_tmp_path


async def terminate_session(process, stop_fn, timeout: float = 2.0):
    """Terminate a shell session and its process group safely."""
    pgid = None
    try:
        pgid = os.getpgid(process.pid)
    except ProcessLookupError:
        pgid = None

    stop_fn()

    if pgid:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pgid = None

    try:
        await asyncio.wait_for(process.wait(), timeout=timeout)
        return
    except asyncio.TimeoutError:
        if pgid:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                return
        else:
            process.kill()
        await process.wait()
