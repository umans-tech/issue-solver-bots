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

## Table of Contents

1. [Prerequisites](#prerequisites)
    - [GitLab Runner Configuration](#gitlab-runner-configuration)
    - [Access Tokens and API Keys](#access-tokens-and-api-keys)
    - [Project Repository Setup](#project-repository-setup)
2. [Setup](#setup)
    - [Option 1: Quick Integration (Turnkey Solution)](#option-1-quick-integration-turnkey-solution)
    - [Option 2: Custom Integration](#option-2-custom-integration)
3. [Usage](#usage)
    - [Trigger via Merge Request Event](#trigger-via-merge-request-event)
    - [Manual Trigger](#manual-trigger)
        - [Required Variables](#required-variables)
        - [How to Trigger Manually](#how-to-trigger-manually)
    - [Customizing Agents and Models](#customizing-agents-and-models)
        - [Available Agents](#available-agents)
        - [Example](#example)
    - [Docker Configuration](#docker-configuration)
4. [Environment Variables](#environment-variables)
5. [Detailed Steps in `solve-issues` Job](#detailed-steps-in-solve-issues-job)
6. [FAQ](#faq)
7. [Conclusion](#conclusion)

## Prerequisites

### GitLab Runner Configuration

> [!NOTE]
> Option 1 has been tested and confirmed to work with GitLab.com's shared runners (managed runners), making it
> an excellent choice for users who rely on GitLab's shared CI infrastructure.

- **For Option 1 Users (GitLab.com Managed Runners)**:

    - **No additional runner configuration is required.**
      You can proceed without additional setup.
      Option 1 has been tested and works out-of-the-box ✨ with GitLab.com's shared runners.

- **For Self-Managed Runners**:

    - Ensure you have a GitLab Runner configured to run Docker-in-Docker (DinD).
      This allows the CI job to run Docker commands within Docker.
    - The runner must be configured with the following executor settings:

      ```toml
      privileged = true
      volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
      ```

### Access Tokens and API Keys

Set the following environment variables in your GitLab project **Settings > CI/CD > Variables**:

| Variable Name               | Description                                                                                | Required                    | Default |
|-----------------------------|--------------------------------------------------------------------------------------------|-----------------------------|---------|
| `CODING_AGENT_ACCESS_TOKEN` | GitLab personal access token with API scope. Used by the agent to commit and push changes. | **Yes**                     | N/A     |
| `OPENAI_API_KEY`            | OpenAI API key to access language models. Required if using OpenAI models.                 | **Yes** (if using OpenAI)   | N/A     |
| `DEEPSEEK_API_BASE_URL`     | Base URL for DeepSeek API. Required if using DeepSeek models.                              | **Yes** (if using DeepSeek) | N/A     |
| `DEEPSEEK_API_KEY`          | API key for DeepSeek services. Required if using DeepSeek models.                          | **Yes** (if using DeepSeek) | N/A     |
| `MODEL_NAME`                | Name of the model to use.                                                                  | No                          | `gpt4o` |

> [!IMPORTANT] 
> Ensure that your `CODING_AGENT_ACCESS_TOKEN` has the necessary permissions to commit and push
> changes to your repository.

### Project Repository Setup

- Ensure that the repository is properly initialized and that the agent has the necessary permissions to push changes.
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

This option has been **tested and confirmed to work with GitLab.com's shared runners**. It's ideal for getting started
quickly without any additional runner configuration.

#### Steps

1. **Include the Template**

   Add the include statement to your `.gitlab-ci.yml` file as shown above.

2. **Set Required Environment Variables**

   In your project's **Settings > CI/CD > Variables**, add the necessary variables as per
   the [Access Tokens and API Keys](#access-tokens-and-api-keys) section.

3. **Run the Pipeline**

    - Create a new merge request or trigger the pipeline manually as described in the [Usage](#usage) section.

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

Extend the `solve-issues` template and override the necessary variables in your `.gitlab-ci.yml`.
Specify the variables you want to customize under the `variables` section:

```yaml
solve-issues:
  variables:
    AGENT: SWE-crafter        # Options: SWE-agent (default), SWE-crafter
    MODEL_NAME: gpt-3.5-turbo # Replace with your preferred model
    DOCKER_DRIVER: overlay2
    DOCKER_HOST: "tcp://docker:2375"
  extends:
    - .solve-issues
```

#### Step 3: Assign the Job to a Stage

Ensure the `solve-issues` job is assigned to the appropriate stage in your pipeline:

```yaml
stages:
  - code
  - test
```

#### Step 4: Set Environment Variables

Add or override any necessary environment variables in your project's **Settings > CI/CD > Variables**, as per
the [Access Tokens and API Keys](#access-tokens-and-api-keys) section.

> [!CAUTION] 
> If you are using self-managed runners, ensure they are configured with Docker-in-Docker support as
> described in the [GitLab Runner Configuration](#gitlab-runner-configuration) section.

## Usage

### Trigger via Merge Request Event

The `solve-issues` job can automatically run when a merge request is created. It will proceed if:

- The **merge request description is not empty**.
- **No files have been changed** in the merge request.

This is useful for creating a placeholder merge request that the agent will populate with code changes based on the
description.

#### Steps

1. **Create a New Merge Request**

    - Ensure the merge request description contains a clear and detailed description of the issue to be resolved.

2. **Do Not Include Any File Changes**

    - The merge request should not include any changes to files. The agent will handle code changes.

3. **Submit the Merge Request**

    - Upon submission, the `solve-issues` job will be triggered automatically.

> [!TIP] 
> Use the merge request title to summarize the issue, which will be used in commit messages.

### Manual Trigger

You can manually trigger the `solve-issues` job from the GitLab UI or API by specifying issue-related variables.

#### Required Variables

At least one of the following variables must be provided when triggering the job manually:

- **`GITLAB_ISSUE_ID`**: The ID of the GitLab issue to resolve.
- **`ISSUE_URL`**: The URL of the issue.
- **`ISSUE_DESCRIPTION`**: A description of the issue to resolve.

#### How to Trigger Manually

1. **Navigate to Pipelines**

    - Go to **CI/CD > Pipelines** in your GitLab project.

2. **Run Pipeline**

    - Click on **Run pipeline**.

3. **Set Variables**

    - In the **Variables** section, add the necessary variables. For example:

      | Variable            | Value                                        |
      |---------------------|----------------------------------------------|
      | `GITLAB_ISSUE_ID`   | `123`                                        |
      | `ISSUE_URL`         | `https://gitlab.com/your-project/issues/123` |
      | `ISSUE_DESCRIPTION` | `Description of the issue to resolve`        |

4. **Run the Job**

    - Click **Run pipeline** to start the job.

> [!IMPORTANT] 
> Ensure that the `CODING_AGENT_ACCESS_TOKEN` has permissions to access the issue if using
`GITLAB_ISSUE_ID` or `ISSUE_URL`.

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

> [!TIP] 
> Experiment with different agents and models to find the best fit for your project's needs.

### Docker Configuration

The job uses Docker-in-Docker. Customize Docker settings if necessary.

#### Example

```yaml
solve-issues:
  variables:
    DOCKER_DRIVER: overlay2
    DOCKER_HOST: "tcp://docker:2375"
```

> [!CAUTION] 
> Modifying Docker settings may require changes to your runner configuration.

## Environment Variables

Below is a summary of all the environment variables used in the `solve-issues` job:

| Variable Name               | Description                                                                                | Required                    | Default             |
|-----------------------------|--------------------------------------------------------------------------------------------|-----------------------------|---------------------|
| `AGENT`                     | Agent to use (`SWE-agent` or `SWE-crafter`).                                               | No                          | `SWE-agent`         |
| `MODEL_NAME`                | Name of the model to use.                                                                  | No                          | `gpt4o`             |
| `CODING_AGENT_ACCESS_TOKEN` | GitLab personal access token with API scope. Used by the agent to commit and push changes. | **Yes**                     | N/A                 |
| `OPENAI_API_KEY`            | OpenAI API key to access language models. Required if using OpenAI models.                 | **Yes** (if using OpenAI)   | N/A                 |
| `DEEPSEEK_API_BASE_URL`     | Base URL for DeepSeek API. Required if using DeepSeek models.                              | **Yes** (if using DeepSeek) | N/A                 |
| `DEEPSEEK_API_KEY`          | API key for DeepSeek services. Required if using DeepSeek models.                          | **Yes** (if using DeepSeek) | N/A                 |
| `DOCKER_DRIVER`             | Docker storage driver.                                                                     | No                          | `overlay2`          |
| `DOCKER_HOST`               | Docker host address.                                                                       | No                          | `tcp://docker:2375` |

## Detailed Steps in `solve-issues` Job

1. **Environment Setup**

    - Installs required packages: Docker, Git, `jq`, and `curl`.
    - Configures Git for committing changes.

2. **Condition Checks**

    - **Merge Requests**

        - Checks if the description is present and no files have been changed.
        - Proceeds if conditions are met; otherwise, exits gracefully.

    - **Manual Triggers**

        - Checks if at least one of `GITLAB_ISSUE_ID`, `ISSUE_URL`, or `ISSUE_DESCRIPTION` is provided.
        - Fetches issue description if `GITLAB_ISSUE_ID` is provided.

3. **Preparing Issue Data**

    - Creates a markdown file (`issue_description.md`) containing the issue description.

4. **Agent Selection**

    - Determines the Docker images to use based on the `AGENT` variable.
    - Supports agents like SWE-agent and SWE-crafter.

5. **Pulling Docker Images**

    - Pulls the necessary agent and runner Docker images from Docker Hub.

6. **Generating Patch**

    - Runs the agent to generate code changes based on the issue description.
    - Uses the specified `MODEL_NAME` for the language model.

7. **Applying Changes**

    - Applies the generated patch to the codebase.
    - Displays the changes using `git diff`.

8. **Committing and Pushing Changes**

    - Configures Git with the agent's user name and email.
    - Commits the changes with an automated message.
    - Pushes the commit to the repository using the `CODING_AGENT_ACCESS_TOKEN`.

## FAQ

**Q1: What permissions are required for the `CODING_AGENT_ACCESS_TOKEN`?**

- **A**: The token must have API scope and permissions to push to the repository branches where changes will be made.

**Q2: Can I use this setup with self-managed GitLab instances?**

- **A**: Yes, but you need to ensure that your runners are configured properly with Docker-in-Docker support.

**Q3: What models can I use with this setup?**

- **A**: You can use any model supported by the agent. Common options include `gpt4o` (default), `gpt-3.5-turbo`, or
  models provided by DeepSeek.

**Q4: How do I obtain an OpenAI API key?**

- **A**: You can sign up for an API key on the [OpenAI website](https://platform.openai.com/account/api-keys).

**Q5: What happens if the agent cannot resolve the issue?**

- **A**: The job will complete without pushing any changes. You can check the job logs for details.

**Q6: Is it safe to run Docker-in-Docker on shared runners?**

- **A**: GitLab.com's shared runners are managed securely, and running Docker-in-Docker is supported for jobs that
  require it.

**Q7: Can I trigger the job via the API?**

- **A**: Yes, you can trigger the job via GitLab's API by specifying the necessary variables.

## Conclusion

By integrating the `solve-issues` template into your GitLab CI/CD pipeline, you can automate issue resolution and
enhance your development workflow. Whether you choose the quick integration or customize it to your needs, this setup
allows for flexible and powerful automation using best-in-class agents like SWE-agent and SWE-crafter, with more agents
coming soon.

> [!TIP] 
> Start with Option 1 to quickly see the benefits, and then explore customizations as needed.

If you have any questions or need assistance, please open an issue on
our [GitHub repository](https://github.com/umans-tech/issue-solver-bots/issues).