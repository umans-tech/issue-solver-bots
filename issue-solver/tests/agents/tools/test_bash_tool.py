import pytest

from issue_solver.agents.tools.base import ToolError
from issue_solver.agents.tools.bash import BashTool, _BashSession


@pytest.mark.asyncio
async def test_runs_command_and_collects_stdout_and_stderr(bash_tool):
    # Given
    # When
    result = await bash_tool(command="echo hello && echo err 1>&2")
    # Then
    assert result.output == "hello"
    assert result.error == "err"


@pytest.mark.asyncio
async def test_reports_terminated_shell_needs_restart(bash_tool):
    # Given
    await bash_tool(command="echo start")
    await _terminate_session(bash_tool._session)
    # When
    result = await bash_tool(command="echo next")
    # Then
    assert result.system == "tool must be restarted"
    assert "returncode" in (result.error or "")


@pytest.mark.asyncio
async def test_timeout_marks_session_until_restart(bash_tool):
    # Given
    await bash_tool(command="echo warmup")
    _force_timeout(bash_tool._session)
    # When
    with pytest.raises(ToolError):
        await bash_tool(command="sleep 0.05")
    # Then
    with pytest.raises(ToolError):
        await bash_tool(command="echo after-timeout")
    await bash_tool(restart=True)
    after = await bash_tool(command="echo back")
    assert after.output == "back"


@pytest.mark.asyncio
async def test_errors_when_no_command_provided(bash_tool):
    # Given
    # When / Then
    with pytest.raises(ToolError):
        await bash_tool()


def test_to_params_reports_metadata():
    # Given / When
    tool = BashTool()
    params = tool.to_params()
    # Then
    assert params["name"] == tool.name
    assert params["type"] == tool.api_type


@pytest.mark.asyncio
async def test_session_guardrails_and_idempotent_start():
    # Given
    session = _BashSession()
    # When
    with pytest.raises(ToolError):
        session.stop()
    with pytest.raises(ToolError):
        await session.run("echo nope")
    await session.start()
    first_pid = session._process.pid
    await session.start()
    # Then
    assert session._process.pid == first_pid
    session.stop()
    await session._process.wait()
    session.stop()


async def _terminate_session(session: _BashSession | None):
    if session and session._process.returncode is None:
        session._process.terminate()
        await session._process.wait()


def _force_timeout(session: _BashSession | None):
    if session:
        session._timeout = 0.005
        session._output_delay = 0.0005
