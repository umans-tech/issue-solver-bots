import pytest
from issue_solver.agents.tools.base import ToolError
from tests.agents.tools.conftest import terminate_session


@pytest.mark.asyncio
async def test_lists_repo_and_sees_docs(bash_tool, sample_repo):
    # When
    result = await bash_tool(command=f"cd {sample_repo} && ls -1")
    # Then
    assert "README.md" in result.output
    assert "src" in result.output
    assert "docs" in result.output


@pytest.mark.asyncio
async def test_reads_file_and_captures_stderr(bash_tool, sample_repo):
    # When
    result = await bash_tool(
        command=f"cd {sample_repo} && cat README.md && echo warn 1>&2"
    )
    # Then
    assert result.output.strip() == "hello"
    assert result.error.strip() == "warn"


@pytest.mark.asyncio
async def test_restart_clears_state(bash_tool, sample_repo):
    # Given
    await bash_tool(command=f"cd {sample_repo} && pwd")
    # When
    await bash_tool(restart=True)
    result = await bash_tool(command="pwd")
    # Then
    assert result.output


@pytest.mark.asyncio
async def test_restart_after_shell_exit(bash_tool, sample_repo):
    # Given
    await bash_tool(command=f"cd {sample_repo} && echo warmup")
    await _terminate_session(bash_tool)
    # When
    await bash_tool(restart=True)
    result = await bash_tool(command="pwd")
    # Then
    assert result.output


@pytest.mark.asyncio
async def test_missing_command_raises(bash_tool):
    # When / Then
    with pytest.raises(ToolError):
        await bash_tool()


@pytest.mark.asyncio
async def test_timeout_requests_restart(bash_tool, sample_repo):
    # Given
    await bash_tool(command=f"cd {sample_repo} && echo ready")
    bash_tool._session._timeout = 0.01
    # When / Then
    with pytest.raises(ToolError) as exc:
        await bash_tool(command="sleep 0.1")
    assert "timed out" in str(exc.value)


@pytest.mark.asyncio
async def test_run_after_exit_signals_restart(bash_tool, sample_repo):
    # Given
    await bash_tool(command=f"cd {sample_repo} && echo warmup")
    await _terminate_session(bash_tool)
    # When
    result = await bash_tool(command="pwd")
    # Then
    assert result.error


async def _terminate_session(tool):
    if tool._session and tool._session._process:
        await terminate_session(tool._session._process, tool._session.stop)
