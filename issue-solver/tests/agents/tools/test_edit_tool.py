import pytest
from pathlib import Path

from issue_solver.agents.tools.base import ToolError
from issue_solver.agents.tools.edit import EditTool


@pytest.mark.asyncio
async def test_end_to_end_edit_flow(abs_tmp_path: Path, edit_tool: EditTool):
    # Given
    path = abs_tmp_path / "note.txt"

    # When
    create = await edit_tool(command="create", path=str(path), file_text="one\ntwo")
    view = await edit_tool(command="view", path=str(path))
    insert = await edit_tool(
        command="insert", path=str(path), insert_line=1, new_str="middle"
    )
    replace = await edit_tool(
        command="str_replace", path=str(path), old_str="middle", new_str="MID"
    )
    undo1 = await edit_tool(command="undo_edit", path=str(path))
    undo2 = await edit_tool(command="undo_edit", path=str(path))

    # Then
    assert "File created successfully" in create.output
    assert "1\tone" in view.output and "2\ttwo" in view.output
    assert "middle" in insert.output
    assert "MID" in replace.output
    assert path.read_text() == "one\ntwo"
    assert "Last edit to" in undo1.output and "Last edit to" in undo2.output


def test_to_params_reports_name_and_type(edit_tool: EditTool):
    params = edit_tool.to_params()
    assert params["name"] == edit_tool.name
    assert params["type"] == edit_tool.api_type


@pytest.mark.parametrize(
    "command,kwargs",
    [
        ("create", {"file_text": None}),
        ("str_replace", {"new_str": "x"}),  # missing old_str
        ("insert", {"new_str": "x"}),  # missing insert_line
        ("insert", {"insert_line": 0}),  # missing new_str
    ],
)
@pytest.mark.asyncio
async def test_missing_required_arguments(
    abs_tmp_path: Path, edit_tool: EditTool, command, kwargs
):
    # Given
    path = abs_tmp_path / "missing.txt"
    path.write_text("line")

    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command=command, path=str(path), **kwargs)


@pytest.mark.parametrize(
    "path_setup,command,kwargs",
    [
        (lambda base: "relative.txt", "view", {}),
        (lambda base: base / "does-not-exist.txt", "view", {}),
        (lambda base: base, "insert", {"insert_line": 0, "new_str": "x"}),  # dir misuse
        (
            lambda base: (base / "exists.txt").write_text("x") or (base / "exists.txt"),
            "create",
            {"file_text": "new"},
        ),  # create overwrite
    ],
)
@pytest.mark.asyncio
async def test_path_validation_errors(
    abs_tmp_path: Path, edit_tool: EditTool, path_setup, command, kwargs
):
    # Given
    target = path_setup(abs_tmp_path)

    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command=command, path=str(target), **kwargs)


@pytest.mark.parametrize(
    "view_range",
    [
        [1],  # wrong length
        [2, 1],  # end < start
        [0, 1],  # start < 1
        [4, 5],  # start > n_lines
        [1, 99],  # end > n_lines
    ],
)
@pytest.mark.asyncio
async def test_view_range_invalid(abs_tmp_path: Path, edit_tool: EditTool, view_range):
    # Given
    path = abs_tmp_path / "range-invalid.txt"
    path.write_text("a\nb\nc")

    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(path), view_range=view_range)


@pytest.mark.parametrize(
    "view_range, expected",
    [
        ([1, 1], "1\tl1"),
        ([2, -1], "2\tl2"),
    ],
)
@pytest.mark.asyncio
async def test_view_range_valid_slices(
    abs_tmp_path: Path, edit_tool: EditTool, view_range, expected
):
    # Given
    path = abs_tmp_path / "slice.txt"
    path.write_text("l1\nl2\nl3")

    # When
    result = await edit_tool(command="view", path=str(path), view_range=view_range)

    # Then
    assert expected in result.output


@pytest.mark.asyncio
async def test_directory_view_and_guardrails(abs_tmp_path: Path, edit_tool: EditTool):
    # Given
    directory = abs_tmp_path / "dir"
    directory.mkdir()
    (directory / "file.txt").write_text("content")

    # When
    result = await edit_tool(command="view", path=str(directory))

    # Then
    assert "files and directories up to 2 levels deep" in result.output
    assert "file.txt" in result.output
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(directory), view_range=[1, 2])


@pytest.mark.parametrize(
    "content, old_str, new_str, expected_error_fragment",
    [
        ("only one line", "missing", "x", "did not appear"),
        ("a\na\n", "a", "b", "Multiple occurrences"),
    ],
)
@pytest.mark.asyncio
async def test_str_replace_error_paths(
    abs_tmp_path: Path,
    edit_tool: EditTool,
    content,
    old_str,
    new_str,
    expected_error_fragment,
):
    # Given
    path = abs_tmp_path / "replace.txt"
    path.write_text(content)
    edit_tool._file_history[path].clear()

    # When
    with pytest.raises(ToolError) as excinfo:
        await edit_tool(
            command="str_replace", path=str(path), old_str=old_str, new_str=new_str
        )
    # Then
    assert expected_error_fragment in str(excinfo.value)
    with pytest.raises(ToolError):
        await edit_tool(command="undo_edit", path=str(path))


@pytest.mark.asyncio
async def test_insert_at_file_end(abs_tmp_path: Path, edit_tool: EditTool):
    # Given
    path = abs_tmp_path / "append.txt"
    path.write_text("a\nb")

    # When
    result = await edit_tool(
        command="insert", path=str(path), insert_line=2, new_str="c"
    )

    # Then
    assert "c" in result.output
    assert path.read_text() == "a\nb\nc"


@pytest.mark.asyncio
async def test_insert_out_of_range(abs_tmp_path: Path, edit_tool: EditTool):
    # Given
    path = abs_tmp_path / "insert-range.txt"
    path.write_text("a\nb")

    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="insert", path=str(path), insert_line=99, new_str="x")


@pytest.mark.asyncio
async def test_create_requires_file_text(abs_tmp_path: Path, edit_tool: EditTool):
    # Given
    path = abs_tmp_path / "create-missing.txt"

    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="create", path=str(path))


@pytest.mark.asyncio
async def test_unknown_command_raises(abs_tmp_path: Path, edit_tool: EditTool):
    # Given
    path = abs_tmp_path / "unknown.txt"
    path.write_text("data")

    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command=None, path=str(path))


def test_read_write_errors_are_wrapped(tmp_path: Path):
    # Given
    tool = EditTool()

    # When / Then
    with pytest.raises(ToolError):
        tool.read_file(tmp_path)
    with pytest.raises(ToolError):
        tool.write_file(tmp_path, "data")
