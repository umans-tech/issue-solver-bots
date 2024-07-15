# GitLab CI Setup for issue-solver-bots

## Introduction

The `solve-issues` template provided by issue-solver-bots automates the resolution of issues using SWE-agent. This
template can be easily integrated into your existing GitLab CI/CD pipelines to enhance and innovate your development
workflow without compromising security or requiring large-scale migrations.

## Features

- 🛠️ Automates issue resolution via SWE-agent.
- 🔍 Supports resolving issues by ID or description.
- 🚀 Can be triggered manually or through merge request events.
- 🔗 Integrates seamlessly with GitLab projects.
- ⚙️ Uses the `MODEL_NAME` environment variable to specify the model, defaulting to `gpt4o`.

## Prerequisites

1. **GitLab Runner**: Ensure you have a GitLab Runner configured to run Docker.
2. **Access Tokens**: Set up the following environment variables in your GitLab CI/CD settings:
    - `CODING_AGENT_ACCESS_TOKEN`: Personal access token with access to your GitLab project.
    - `OPENAI_API_KEY`: API key for accessing OpenAI services.
    - `MODEL_NAME` (optional): Name of the model to use (default is `gpt4o`).

## Setup

### Include the Template in Your `.gitlab-ci.yml`

Add the following line to your `.gitlab-ci.yml` to include the `solve-issues` template:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/umans-tech/issue-solver-bots/main/gitlab-ci/solve-issues.yml'
```

### Configure Your Pipeline

Configure your pipeline to use the `solve-issues` job. An example configuration is shown below:

```yaml
stages:
  - code
  - test

include:
  - remote: 'https://raw.githubusercontent.com/umans-tech/issue-solver-bots/main/gitlab-ci/solve-issues.yml'

unit-test-job:
  image: python:3.10-alpine
  stage: test
  before_script:
    - pip install -e ".[dev]"
  script:
    - pytest
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_TAG'
    - when: manual
```

## Usage

### Merge Request Event

When a merge request is created, the `solve-issues` job will check if the merge request description is empty and if no
files have been changed. If these conditions are met, the job will proceed to resolve the issue.

### Manual Trigger

You can manually trigger the `solve-issues` job by specifying issue-related variables:

- `GITLAB_ISSUE_ID`: The ID of the GitLab issue to be resolved.
- `ISSUE_URL`: The URL of the issue.
- `ISSUE_DESCRIPTION`: A description of the issue to be resolved.

#### Example

To trigger the job manually, go to your project's CI/CD pipelines, click on "Run pipeline", and set the necessary
variables:

- **GITLAB_ISSUE_ID**: `123`
- **ISSUE_URL**: `https://gitlab.com/your-project/issues/123`
- **ISSUE_DESCRIPTION**: `Description of the issue to resolve`

### Detailed Steps in `solve-issues` Job

1. **Checking Conditions**: The job checks the conditions for automated coding based on merge request or manual trigger
   parameters.
2. **Creating Data Path**: It creates a markdown file containing the issue description.
3. **Pulling Docker Images**: The required Docker images are pulled.
4. **Generating Patch**: The job runs the SWE-agent to generate a patch based on the issue description, using the
   selected model (specified by the `MODEL_NAME` environment variable, defaulting to `gpt4o` if not set).
5. **Committing Changes**: The changes are committed and pushed back to the repository.

## Conclusion

By integrating the `solve-issues` template into your GitLab CI/CD pipeline, you can automate the resolution of issues
and enhance your development workflow without compromising security or undergoing massive migrations. If you have any
questions or need further assistance, feel free to open an issue on
our [GitHub repository](https://github.com/umans-tech/issue-solver-bots/issues).
