# GitLab CI Setup for issue-solver-bots

## Introduction

The `solve-issues` template provided by issue-solver-bots automates the resolution of issues using best-in-class agents
like **SWE-agent** and **SWE-crafter**, with more coming soon.
This template can be easily integrated into your existing GitLab CI/CD pipelines to enhance and innovate your
development workflow without compromising security or requiring large-scale migrations.

## Features

- 🛠️ **Automated Issue Resolution**: Leverages advanced agents like SWE-agent and SWE-crafter
  to automatically resolve issues.
- 🔍 **Flexible Triggers**: Supports resolving issues by ID, URL, or description.
- 🚀 **Multiple Execution Modes**: Can be triggered manually or through merge request events.
- 🔗 **Seamless Integration**: Works with any GitLab project without extensive setup.
- ⚙️ **Customizable Agents and Models**: Choose between different agents and models to suit your needs.
- 📦 **Isolated Execution**: Utilizes Docker-in-Docker for secure and isolated job execution.

## Prerequisites

1. **GitLab Runner with Docker-in-Docker Support**:

    - **Option 1 Users**: If you are using GitLab.com's shared runners (managed runners), you can proceed without
      additional setup. Option 1 has been tested and works out-of-the-box with GitLab.com's shared runners.
    - **Self-Managed Runners**: Ensure you have a GitLab Runner configured to run Docker-in-Docker (DinD).
      This allows the CI job to run Docker commands within Docker.
        - The runner must be configured with the following executor settings:
            - `privileged = true`
            - `volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]`

2. **Access Tokens and API Keys**:

    - **`CODING_AGENT_ACCESS_TOKEN`** (**Required**): A GitLab personal access token with API scope. This token is used
      by the agent to commit and push changes to your repository.
    - **`OPENAI_API_KEY`** (**Required if using OpenAI models**): Your OpenAI API key to access language models.
    - **`DEEPSEEK_API_BASE_URL`** and **`DEEPSEEK_API_KEY`** (**Required if using DeepSeek models**): Credentials for
      accessing DeepSeek services.
    - **`MODEL_NAME`** (**Optional**): The name of the model to use. Defaults to `gpt4o` if not specified.

3. **Project Repository Setup**:

    - Ensure that the repository is properly initialized and that the agent has the necessary permissions to push
      changes.
    - The default branch should be protected appropriately to allow the agent to push changes.

## Setup

### Option 1: Quick Integration (Turnkey Solution)

**Tested with GitLab.com Managed Runners**

For a straightforward setup without customization, include the `solve-issues` template directly in your
`.gitlab-ci.yml`:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/umans-tech/issue-solver-bots/main/gitlab-ci/solve-issues.yml'
```

This option has been **tested and confirmed to work with GitLab.com's shared runners**.
It's ideal for getting started quickly without any additional runner configuration.

#### Steps:

1. **Include the Template**:

   Add the include statement to your `.gitlab-ci.yml` file as shown above.

2. **Set Required Environment Variables**:

   In your project's **Settings > CI/CD > Variables**, add the following variables:

    - **`CODING_AGENT_ACCESS_TOKEN`**: Your GitLab personal access token with API scope.
    - **`OPENAI_API_KEY`**: Your OpenAI API key (if using OpenAI models).

3. **Run the Pipeline**:

    - Create a new merge request or trigger the pipeline manually as described in the **Usage** section.

### Option 2: Custom Integration

If you need to customize the agent, model, or Docker configurations, you can include the template and override the
necessary variables.

#### Step 1: Include the Template

Add the following to your `.gitlab-ci.yml`:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/umans-tech/issue-solver-bots/main/gitlab-ci/solve-issues.yml'
```

#### Step 2: Override Variables

Specify the variables you want to customize under the `variables` section:

```yaml
solve-issues:
  variables:
    AGENT: SWE-crafter        # Options: SWE-agent (default), SWE-crafter
    MODEL_NAME: gpt-3.5-turbo # Replace with your preferred model
    DOCKER_DRIVER: overlay2
    DOCKER_HOST: "tcp://docker:2375"
```

#### Step 3: Assign the Job to a Stage

Ensure the `solve-issues` job is assigned to the appropriate stage in your pipeline:

```yaml
stages:
  - code
  - test
```

#### Note for Self-Managed Runners

If you are using self-managed runners, ensure they are configured with Docker-in-Docker support as described in the *
*Prerequisites** section.

## Usage

### Trigger via Merge Request Event

The `solve-issues` job can automatically run when a merge request is created. It will proceed if:

- The **merge request description is not empty**.
- **No files have been changed** in the merge request.

This is useful for creating a placeholder merge request that the agent will populate with code changes based on the
description.

### Manual Trigger

You can manually trigger the `solve-issues` job from the GitLab UI or API by specifying issue-related variables.

#### Required Variables

At least one of the following variables must be provided when triggering the job manually:

- **`GITLAB_ISSUE_ID`**: The ID of the GitLab issue to resolve.
- **`ISSUE_URL`**: The URL of the issue.
- **`ISSUE_DESCRIPTION`**: A description of the issue to resolve.

#### How to Trigger Manually

1. Navigate to **CI/CD > Pipelines** in your GitLab project.
2. Click on **Run pipeline**.
3. In the **Variables** section, add the necessary variables:

    - **`GITLAB_ISSUE_ID`**: e.g., `123`
    - **`ISSUE_URL`**: e.g., `https://gitlab.com/your-project/issues/123`
    - **`ISSUE_DESCRIPTION`**: Provide a detailed description.

4. Click **Run pipeline** to start the job.

### Customizing Agents and Models

You can customize the agent and model used for issue resolution by setting the `AGENT` and `MODEL_NAME` variables.

#### Available Agents

- **`SWE-agent`** (default): A general-purpose software engineering agent.
- **`SWE-crafter`**: An alternative agent with different capabilities.
- **More agents coming soon!**

#### Example

```yaml
solve-issues:
  variables:
    AGENT: SWE-crafter
    MODEL_NAME: gpt-3.5-turbo
```

### Docker Configuration

The job uses Docker-in-Docker. Customize Docker settings if necessary.

#### Example

```yaml
solve-issues:
  variables:
    DOCKER_DRIVER: overlay2
    DOCKER_HOST: "tcp://docker:2375"
```

## Detailed Steps in `solve-issues` Job

1. **Environment Setup**:

    - Installs required packages: Docker, Git, `jq`, and `curl`.
    - Configures Git for committing changes.

2. **Condition Checks**:

    - For merge requests: Checks if the description is present and no files have been changed.
    - For manual triggers: Checks if at least one of `GITLAB_ISSUE_ID`, `ISSUE_URL`, or `ISSUE_DESCRIPTION` is provided.

3. **Preparing Issue Data**:

    - Creates a markdown file (`issue_description.md`) with the issue description.

4. **Agent Selection**:

    - Determines the Docker images to use based on the `AGENT` variable.
    - Supports agents like SWE-agent and SWE-crafter.

5. **Pulling Docker Images**:

    - Pulls the necessary agent and runner Docker images.

6. **Generating Patch**:

    - Runs the agent to generate code changes based on the issue description.
    - Uses the specified `MODEL_NAME` for the language model.

7. **Applying Changes**:

    - Applies the generated patch to the codebase.
    - Shows the changes using `git diff`.

8. **Committing and Pushing Changes**:

    - Commits the changes with an automated message.
    - Pushes the commit to the repository.

## Conclusion

By integrating the `solve-issues` template into your GitLab CI/CD pipeline, you can automate issue resolution and
enhance your development workflow. Whether you choose the quick integration or customize it to your needs, this setup
allows for flexible and powerful automation using best-in-class agents like SWE-agent and SWE-crafter, with more agents
coming soon.

**Note**: Option 1 is tested and confirmed to work with GitLab.com's managed runners, making it an excellent choice for
users who rely on GitLab's shared CI infrastructure.

If you have any questions or need assistance, please open an issue on
our [GitHub repository](https://github.com/umans-tech/issue-solver-bots/issues).