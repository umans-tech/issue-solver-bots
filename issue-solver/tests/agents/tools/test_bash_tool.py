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
    session = bash_tool._session
    session._process.terminate()
    await session._process.wait()

    # When
    result = await bash_tool(command="echo next")

    # Then
    assert result.system == "tool must be restarted"
    assert f"{session._process.returncode}" in (result.error or "")


@pytest.mark.asyncio
async def test_timeout_marks_session_until_restart(bash_tool):
    # Given
    await bash_tool(command="echo warmup")
    session = bash_tool._session
    session._timeout = 0.005
    session._output_delay = 0.0005

    # When
    with pytest.raises(ToolError):
        await bash_tool(command="sleep 0.05")

    # Then
    with pytest.raises(ToolError):
        await bash_tool(command="echo after-timeout")

    restarted = await bash_tool(restart=True)
    assert restarted.system == "tool has been restarted."
    after = await bash_tool(command="echo back")
    assert after.output == "back"


@pytest.mark.asyncio
async def test_errors_when_no_command_provided(bash_tool):
    # Given
    with pytest.raises(ToolError):
        await bash_tool()


def test_to_params_reports_metadata():
    tool = BashTool()
    params = tool.to_params()
    assert params["name"] == tool.name
    assert params["type"] == tool.api_type


@pytest.mark.asyncio
async def test_session_guardrails_and_idempotent_start():
    session = _BashSession()

    # Given
    with pytest.raises(ToolError):
        session.stop()

    # When
    with pytest.raises(ToolError):
        await session.run("echo nope")

    # When
    await session.start()
    first_pid = session._process.pid
    await session.start()
    assert session._process.pid == first_pid

    # Then
    session.stop()
    await session._process.wait()
    session.stop()
