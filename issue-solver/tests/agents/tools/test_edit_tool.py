import pytest
from pathlib import Path

from issue_solver.agents.tools.base import ToolError
from issue_solver.agents.tools.edit import EditTool


@pytest.mark.asyncio
async def test_end_to_end_edit_flow(abs_tmp_path: Path, edit_tool: EditTool):
    # Given an absolute path and new editor tool
    path = abs_tmp_path / "note.txt"

    # When we create and view the file
    create = await edit_tool(command="create", path=str(path), file_text="one\ntwo")
    view = await edit_tool(command="view", path=str(path))

    # Then the file is persisted and numbered output is returned
    assert "File created successfully" in create.output
    assert "1\tone" in view.output
    assert "2\ttwo" in view.output

    # When we insert, replace, and undo twice
    insert = await edit_tool(
        command="insert", path=str(path), insert_line=1, new_str="middle"
    )
    replace = await edit_tool(
        command="str_replace", path=str(path), old_str="middle", new_str="MID"
    )
    undo1 = await edit_tool(command="undo_edit", path=str(path))
    undo2 = await edit_tool(command="undo_edit", path=str(path))

    # Then the file content evolves and unwinds as expected
    assert "middle" in insert.output
    assert "MID" in replace.output
    assert path.read_text() == "one\ntwo"
    assert "Last edit to" in undo1.output
    assert "Last edit to" in undo2.output


def test_to_params_reports_name_and_type(edit_tool: EditTool):
    params = edit_tool.to_params()
    assert params["name"] == edit_tool.name
    assert params["type"] == edit_tool.api_type


@pytest.mark.asyncio
async def test_validation_and_uniqueness_errors(
    abs_tmp_path: Path, edit_tool: EditTool
):
    path = abs_tmp_path / "dupes.txt"
    path.write_text("a\na\n")

    # Given a relative path, view should fail
    with pytest.raises(ToolError):
        await edit_tool(command="view", path="relative.txt")

    # Given multiple matches, str_replace should reject the edit
    edit_tool._file_history[path].clear()
    with pytest.raises(ToolError) as excinfo:
        await edit_tool(command="str_replace", path=str(path), old_str="a", new_str="b")
    assert "Multiple occurrences" in str(excinfo.value)

    # Given an out-of-range insert line, it should raise with bounds
    with pytest.raises(ToolError) as excinfo:
        await edit_tool(command="insert", path=str(path), insert_line=99, new_str="z")
    assert "Invalid `insert_line` parameter" in str(excinfo.value)
    assert "range of lines of the file" in str(excinfo.value)


@pytest.mark.asyncio
async def test_directory_view_and_range_guardrails(
    abs_tmp_path: Path, edit_tool: EditTool
):
    directory = abs_tmp_path / "dir"
    directory.mkdir()
    (directory / "file.txt").write_text("content")

    # Given a directory path, view lists files via find
    result = await edit_tool(command="view", path=str(directory))
    assert "files and directories up to 2 levels deep" in result.output
    assert "file.txt" in result.output

    # view_range is not allowed for directories
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(directory), view_range=[1, 2])


@pytest.mark.asyncio
async def test_view_range_and_create_validation(
    abs_tmp_path: Path, edit_tool: EditTool
):
    path = abs_tmp_path / "range.txt"
    path.write_text("line1\nline2")

    # invalid view_range ordering
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(path), view_range=[2, 1])

    # final line beyond file length
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(path), view_range=[1, 99])

    # create should refuse to overwrite existing files
    with pytest.raises(ToolError):
        await edit_tool(command="create", path=str(path), file_text="new")

    # init_line outside file bounds
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(path), view_range=[0, 1])

    # open-ended view_range (-1) slices to file end
    result = await edit_tool(command="view", path=str(path), view_range=[2, -1])
    assert "2\tline2" in result.output


@pytest.mark.asyncio
async def test_str_replace_missing_and_undo_empty_history(
    abs_tmp_path: Path, edit_tool: EditTool
):
    path = abs_tmp_path / "replace.txt"
    path.write_text("only one line")

    with pytest.raises(ToolError) as excinfo:
        await edit_tool(
            command="str_replace", path=str(path), old_str="missing", new_str="x"
        )
    assert "did not appear" in str(excinfo.value)

    # undo should fail when nothing was edited
    with pytest.raises(ToolError):
        await edit_tool(command="undo_edit", path=str(path))


@pytest.mark.asyncio
async def test_insert_at_file_end(abs_tmp_path: Path, edit_tool: EditTool):
    path = abs_tmp_path / "append.txt"
    path.write_text("a\nb")

    result = await edit_tool(
        command="insert", path=str(path), insert_line=2, new_str="c"
    )
    assert "c" in result.output
    assert path.read_text() == "a\nb\nc"


@pytest.mark.asyncio
async def test_missing_required_arguments_and_path_checks(
    abs_tmp_path: Path, edit_tool: EditTool
):
    path = abs_tmp_path / "missing.txt"

    # create without file_text
    with pytest.raises(ToolError):
        await edit_tool(command="create", path=str(path))

    # str_replace without old_str
    with pytest.raises(ToolError):
        await edit_tool(command="str_replace", path=str(path), new_str="x")

    # insert without insert_line or new_str
    path.write_text("line")
    with pytest.raises(ToolError):
        await edit_tool(command="insert", path=str(path), new_str="x")
    with pytest.raises(ToolError):
        await edit_tool(command="insert", path=str(path), insert_line=0)

    # non-existent path with non-create command
    missing_path = abs_tmp_path / "does-not-exist.txt"
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(missing_path))

    # directory path with non-view command
    with pytest.raises(ToolError):
        await edit_tool(
            command="insert", path=str(abs_tmp_path), insert_line=0, new_str="x"
        )


def test_read_write_errors_are_wrapped(tmp_path: Path, monkeypatch):
    tool = EditTool()

    dir_path = tmp_path
    # read_file on a directory raises wrapped ToolError
    with pytest.raises(ToolError):
        tool.read_file(dir_path)

    # write_file failure is wrapped too (writing to a directory)
    with pytest.raises(ToolError):
        tool.write_file(dir_path, "data")


@pytest.mark.asyncio
async def test_old_str_required_and_unknown_command(
    abs_tmp_path: Path, edit_tool: EditTool
):
    path = abs_tmp_path / "file.txt"
    path.write_text("data")

    with pytest.raises(ToolError):
        await edit_tool(command="str_replace", path=str(path), new_str="x")

    with pytest.raises(ToolError):
        await edit_tool(command=None, path=str(path))


@pytest.mark.asyncio
async def test_view_range_requires_two_ints_and_handles_exact_slice(
    abs_tmp_path: Path, edit_tool: EditTool
):
    path = abs_tmp_path / "slice.txt"
    path.write_text("l1\nl2\nl3")

    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(path), view_range=[1])  # wrong length

    result = await edit_tool(command="view", path=str(path), view_range=[1, 1])
    assert "1\tl1" in result.output
    assert "2\t" not in result.output
