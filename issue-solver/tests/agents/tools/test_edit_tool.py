import pytest
from pathlib import Path

from issue_solver.agents.tools.base import ToolError
from issue_solver.agents.tools.edit import EditTool


@pytest.mark.asyncio
async def test_edits_and_undoes_working_copy(sample_repo: Path, edit_tool: EditTool):
    # Given
    checklist = sample_repo / "docs" / "checklist.md"
    checklist.parent.mkdir(parents=True, exist_ok=True)
    original_text = "title\nitem one\nitem two\n"
    # When
    await edit_tool(command="create", path=str(checklist), file_text=original_text)
    first_view = await edit_tool(command="view", path=str(checklist))
    await edit_tool(
        command="str_replace",
        path=str(checklist),
        old_str="item one",
        new_str="first item",
    )
    await edit_tool(
        command="insert",
        path=str(checklist),
        insert_line=1,
        new_str="introduction\n",
    )
    updated_view = await edit_tool(command="view", path=str(checklist))
    await edit_tool(command="undo_edit", path=str(checklist))
    await edit_tool(command="undo_edit", path=str(checklist))
    # Then
    assert "1\ttitle" in first_view.output
    assert "introduction" in updated_view.output
    assert checklist.read_text() == original_text


@pytest.mark.asyncio
async def test_directory_view_shows_tree(sample_repo: Path, edit_tool: EditTool):
    # Given
    root = sample_repo
    # When
    listing = await edit_tool(command="view", path=str(root))
    # Then
    assert "README.md" in listing.output
    assert "src/app.py" in listing.output
    assert "docs/guide.md" in listing.output


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_range",
    [[2, 1], [0, 1], [1, 10], [1, 2, 3], ["a", 1]],
)
async def test_view_range_rejections(sample_repo: Path, edit_tool: EditTool, bad_range):
    # Given
    path = sample_repo / "range.txt"
    path.write_text("a\nb\nc")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(path), view_range=bad_range)


@pytest.mark.asyncio
async def test_str_replace_requires_unique_match(
    sample_repo: Path, edit_tool: EditTool
):
    # Given
    path = sample_repo / "content.txt"
    path.write_text("line\nline\n")
    # When / Then
    # Then
    with pytest.raises(ToolError):
        await edit_tool(
            command="str_replace", path=str(path), old_str="line", new_str="x"
        )


@pytest.mark.asyncio
async def test_insert_rejects_out_of_bounds(sample_repo: Path, edit_tool: EditTool):
    # Given
    path = sample_repo / "lines.txt"
    path.write_text("a\nb")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="insert", path=str(path), insert_line=99, new_str="z")


@pytest.mark.asyncio
async def test_undo_requires_prior_edits(sample_repo: Path, edit_tool: EditTool):
    # Given
    path = sample_repo / "undo.txt"
    path.write_text("content")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="undo_edit", path=str(path))


@pytest.mark.asyncio
async def test_create_and_view_require_absolute_paths(edit_tool: EditTool):
    # Given
    relative_path = Path("relative.txt")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="view", path=str(relative_path))


@pytest.mark.asyncio
async def test_create_refuses_overwrite(sample_repo: Path, edit_tool: EditTool):
    # Given
    path = sample_repo / "existing.txt"
    path.write_text("present")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="create", path=str(path), file_text="new")


@pytest.mark.asyncio
async def test_view_range_returns_requested_lines(
    sample_repo: Path, edit_tool: EditTool
):
    # Given
    path = sample_repo / "multiline.txt"
    path.write_text("a\nb\nc\nd\n")
    # When
    middle = await edit_tool(command="view", path=str(path), view_range=[2, 3])
    tail = await edit_tool(command="view", path=str(path), view_range=[3, -1])
    # Then
    assert "2\tb" in middle.output and "3\tc" in middle.output
    assert "1\ta" not in middle.output and "4\td" not in middle.output
    assert "3\tc" in tail.output and "4\td" in tail.output
    assert "1\ta" not in tail.output and "2\tb" not in tail.output


@pytest.mark.asyncio
async def test_required_parameters_are_enforced(sample_repo: Path, edit_tool: EditTool):
    # Given
    path = sample_repo / "needs.txt"
    path.write_text("line")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command="create", path=str(path))
    with pytest.raises(ToolError):
        await edit_tool(command="str_replace", path=str(path), new_str="x")
    with pytest.raises(ToolError):
        await edit_tool(command="insert", path=str(path), new_str="x")
    with pytest.raises(ToolError):
        await edit_tool(command="insert", path=str(path), insert_line=0)


@pytest.mark.asyncio
async def test_rejects_edit_commands_on_directory(
    sample_repo: Path, edit_tool: EditTool
):
    # Given
    directory = sample_repo / "docs"
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(
            command="insert", path=str(directory), insert_line=0, new_str="x"
        )


@pytest.mark.asyncio
async def test_str_replace_requires_match(sample_repo: Path, edit_tool: EditTool):
    # Given
    path = sample_repo / "nomatch.txt"
    path.write_text("keep\n")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(
            command="str_replace", path=str(path), old_str="gone", new_str="x"
        )


@pytest.mark.asyncio
async def test_unknown_command_is_rejected(sample_repo: Path, edit_tool: EditTool):
    # Given
    path = sample_repo / "file.txt"
    path.write_text("text")
    # When / Then
    with pytest.raises(ToolError):
        await edit_tool(command=None, path=str(path))
