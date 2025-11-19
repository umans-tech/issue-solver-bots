import pytest

from issue_solver.agents.tools.base import ToolError
from issue_solver.agents.tools.bash import BashTool, _BashSession


@pytest.mark.asyncio
async def test_runs_command_and_collects_stdout_and_stderr(bash_tool):
    # Given a fresh bash tool
    # When it runs a simple command
    result = await bash_tool(command="echo hello && echo err 1>&2")
    # Then it returns separate stdout and stderr payloads
    assert result.output == "hello"
    assert result.error == "err"


@pytest.mark.asyncio
async def test_reports_terminated_shell_needs_restart(bash_tool):
    # Given a running session
    await bash_tool(command="echo start")
    session = bash_tool._session
    session._process.terminate()
    await session._process.wait()

    # When we ask it to run again
    result = await bash_tool(command="echo next")

    # Then it tells the agent a restart is needed and carries the exit reason
    assert result.system == "tool must be restarted"
    assert f"{session._process.returncode}" in (result.error or "")


@pytest.mark.asyncio
async def test_timeout_marks_session_until_restart(bash_tool):
    # Given we shrink the timeout to force a quick failure
    await bash_tool(command="echo warmup")
    session = bash_tool._session
    session._timeout = 0.01
    session._output_delay = 0.001

    # When a command exceeds the timeout
    with pytest.raises(ToolError) as excinfo:
        await bash_tool(command="sleep 0.1")
    assert "timed out" in str(excinfo.value)

    # Then subsequent commands still fail until the agent restarts
    with pytest.raises(ToolError):
        await bash_tool(command="echo after-timeout")

    restarted = await bash_tool(restart=True)
    assert restarted.system == "tool has been restarted."
    after = await bash_tool(command="echo back")
    assert after.output == "back"


@pytest.mark.asyncio
async def test_errors_when_no_command_provided(bash_tool):
    # Given the tool is available but no command argument is passed
    with pytest.raises(ToolError):
        await bash_tool()


@pytest.mark.asyncio
async def test_timeout_flag_clears_after_restart(bash_tool):
    # Given we force a timeout to trip the internal _timed_out flag
    await bash_tool(command="echo warmup")
    session = bash_tool._session
    session._timeout = 0.005
    session._output_delay = 0.0005
    with pytest.raises(ToolError):
        await bash_tool(command="sleep 0.05")

    # When we restart, the flag should clear and allow commands again
    await bash_tool(restart=True)
    result = await bash_tool(command="echo ok")
    assert result.output == "ok"


def test_to_params_reports_metadata():
    tool = BashTool()
    params = tool.to_params()
    assert params["name"] == tool.name
    assert params["type"] == tool.api_type


@pytest.mark.asyncio
async def test_run_without_start_raises():
    session = _BashSession()
    with pytest.raises(ToolError):
        await session.run("echo nope")


@pytest.mark.asyncio
async def test_stop_behaviour_before_and_after_process_exit():
    session = _BashSession()
    # stop before start should raise
    with pytest.raises(ToolError):
        session.stop()

    await session.start()
    session.stop()  # stopping a live process should not raise
    await session._process.wait()

    # stop again after process ended should be a no-op
    session.stop()


@pytest.mark.asyncio
async def test_start_is_idempotent():
    session = _BashSession()
    await session.start()
    pid = session._process.pid

    # Calling start again should return immediately and keep the same process
    await session.start()
    assert session._process.pid == pid

    session.stop()
    await session._process.wait()
