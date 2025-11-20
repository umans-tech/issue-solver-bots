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


@pytest.fixture
def sample_repo(abs_tmp_path: Path) -> Path:
    """Tiny repo layout for navigation/editing stories."""
    (abs_tmp_path / "README.md").write_text("hello\n")
    (abs_tmp_path / "src").mkdir()
    (abs_tmp_path / "src" / "app.py").write_text("print('hi')\n")
    (abs_tmp_path / "docs").mkdir()
    (abs_tmp_path / "docs" / "guide.md").write_text("usage\n")
    return abs_tmp_path
