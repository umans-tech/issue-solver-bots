import os
from unittest.mock import Mock

from issue_solver import prepare_solve_issue
from issue_solver.start_resolution import (
    AgentModel,
    SupportedAgent,
    IssueDescription,
    SolveIssueCommand,
    SupportedOpenAPIModel,
    SupportedDeepSeekModel,
)


def test_solve_issue():
    # Given
    patch_generator = Mock()
    solve_issue = prepare_solve_issue(patch_generator)
    os.environ["AGENT_MODEL"] = "gpt-4o"
    os.environ["AGENT_NAME"] = "swe-agent"
    issue_description = """
        Looks like a rounding issue here:
        https://github.com/marshmallow-code/marshmallow/blob/dev/src/marshmallow/fields.py#L1474
        """
    os.environ["ISSUE_DESCRIPTION"] = issue_description

    # When
    solve_issue()

    # Then
    patch_generator.assert_called_once_with(
        SolveIssueCommand(
            model=SupportedOpenAPIModel.GPT4O,
            agent=SupportedAgent.SWE_AGENT,
            issue_description=IssueDescription(issue_description),
        )
    )


def setup(issue_reader):
    def prepare_solve_issue(generate_patch):
        return lambda: generate_patch(
            SolveIssueCommand(
                model=AgentModel(os.environ["AGENT_MODEL"]),
                agent=SupportedAgent(os.environ["AGENT_NAME"]),
                issue_description=issue_reader(),
            )
        )

    return prepare_solve_issue


def test_solve_issue_based_on_gitlab_issue_id():
    # Given
    patch_generator = Mock()
    issue_reader = Mock()
    solve_issue = setup(issue_reader)(patch_generator)
    os.environ["AGENT_MODEL"] = "deepseek-coder"
    os.environ["AGENT_NAME"] = "swe-crafter"
    issue_description = (
        "Looks like a rounding issue here: /src/marshmallow/fields.py#L1474"
    )
    os.environ["GITLAB_ISSUE_ID"] = "123"
    issue_reader.return_value = IssueDescription(issue_description)

    # When
    solve_issue()

    # Then
    patch_generator.assert_called_once_with(
        SolveIssueCommand(
            model=SupportedDeepSeekModel.DEEPSEEK_Coder,
            agent=SupportedAgent.SWE_CRAFTER,
            issue_description=IssueDescription(issue_description),
        )
    )
