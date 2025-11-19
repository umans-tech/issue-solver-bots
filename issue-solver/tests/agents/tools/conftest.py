import pytest
import pytest_asyncio
from pathlib import Path

from issue_solver.agents.tools.bash import BashTool
from issue_solver.agents.tools.edit import EditTool


@pytest_asyncio.fixture
async def bash_tool():
    tool = BashTool()
    yield tool
    if tool._session and tool._session._process.returncode is None:
        tool._session.stop()
        await tool._session._process.wait()


@pytest.fixture
def edit_tool():
    return EditTool()


@pytest.fixture
def abs_tmp_path(tmp_path: Path) -> Path:
    """Resolved tmp_path for absolute-path validations."""
    return tmp_path.resolve()
