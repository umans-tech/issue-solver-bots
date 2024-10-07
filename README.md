# issue-solver-bots

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/umans-tech/issue-solver-bots/ci.yml)
![License](https://img.shields.io/github/license/umans-tech/issue-solver-bots)
![GitHub Stars](https://img.shields.io/github/stars/umans-tech/issue-solver-bots?style=social)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289DA?logo=discord&logoColor=white)](https://discord.gg/wBeQhw9v)

🚀 **Issue-solver-bots** integrates autonomous agents for software development, providing **GitLab CI** and **GitHub
Actions** templates to automatically resolve issues from platforms like GitLab, GitHub, Jira, and Notion. Innovate your
workflow without being locked into a single platform.

## Table of Contents

- [Why Use issue-solver-bots](#why-use-issue-solver-bots)
- [Features](#features)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
- [Usage](#usage)
    - [GitLab CI Integration](#gitlab-ci-integration)
    - [GitHub Actions Integration](#github-actions-integration)
- [Supported Platforms and Agents](#supported-platforms-and-agents)
- [Early Stage and Feedback](#early-stage-and-feedback)
- [FAQ](#faq)
- [Community and Support](#community-and-support)
- [Contribution](#contribution)
- [License](#license)

## Why Use issue-solver-bots

In today's fast-paced development environment, teams often spend valuable time on "Low-Value" (or routine) tasks that
could be automated.
**Issue-solver-bots** empowers your team by:

- **Innovate and Modernize**: Enhance development workflows without being tied to a single platform.
- **Seamless Integration**: Improve existing infrastructure and build processes without overhauling everything or
  compromising security.
- **Avoid Migration Hassles**: Integrate new capabilities without the need for massive migration projects.

## Features

- 🛠️ **CI/CD Templates**: Ready-to-use templates for **GitLab CI** 🦊 and **GitHub Actions** 🐈‍⬛ to automate issue
  resolution using advanced agents like **SWE-agent** and **SWE-crafter**.
- 🔍 **Flexible Issue Resolution**: Resolve issues via their ID, URL, or description (provided as a parameter or through
  MR/PR description).
- 🔗 **Multi-Platform Integration**: Integration with various issue tracking platforms (**GitLab**, **GitHub**). 📝 **Jira
  and Notion integrations coming soon!** 🚧
- 📚 **Comprehensive Documentation**: Detailed guides for quick and efficient setup.
- ⚙️ **Customizable Agents and Models**: Choose between different agents and models to suit your needs.

## Getting Started

### Prerequisites

- **GitLab** or **GitHub** account.
- Access to a **GitLab Runner** or **GitHub Runner** with Docker capabilities.
- **Personal Access Tokens** and **API Keys** as required by the agents.
- **Docker** installed on your runner (if self-hosted).

### Installation

1. **Clone this repository:**

   ```bash
   git clone https://github.com/umans-tech/issue-solver-bots.git
   cd issue-solver-bots
   ```

2. **Review the Documentation:**

    - For **GitLab CI** setup: Refer to [`docs/gitlab-ci-setup.md`](docs/gitlab-ci-setup.md)
    - For **GitHub Actions** setup: Refer to [`docs/github-actions-setup.md`](docs/github-actions-setup.md)

## Usage

### GitLab CI Integration

Integrate with GitLab CI in just a few steps:

1. **Include the Template:**

   Add the following to your project's `.gitlab-ci.yml` file:

   ```yaml
   include:
     - remote: 'https://raw.githubusercontent.com/umans-tech/issue-solver-bots/main/gitlab-ci/solve-issues.yml'
   ```

2. **Set Required Environment Variables:**

   In your project's **Settings > CI/CD > Variables**, add the necessary variables as per
   the [GitLab CI Documentation](docs/gitlab-ci-setup.md).

3. **Trigger the Pipeline:**

    - Create a new merge request with a detailed description, or
    - Manually trigger the pipeline by specifying issue-related variables.

> 💡 **Tip:** Option 1 is tested and confirmed to work with GitLab.com's managed runners, making it an excellent choice
> for users who rely on GitLab's shared CI infrastructure.

### GitHub Actions Integration

Integrate with GitHub Actions easily:

1. **Copy the Workflow File:**

   Copy the provided workflow file into your project's `.github/workflows` directory.

2. **Set Required Secrets:**

   In your repository's **Settings > Secrets and variables > Actions**, add the necessary secrets as per
   the [GitHub Actions Documentation](docs/github-actions-setup.md).

3. **Trigger the Workflow:**

    - Open a new pull request with a detailed description, or
    - Manually trigger the workflow via the Actions tab.

> 🚀 **Tip:** Start by creating a pull request with a clear description of the issue to see the agent in action!

## Supported Platforms and Agents

- **Issue Tracking Platforms:**

    - **GitLab**
    - **GitHub**
    - 📝 **Jira and Notion (coming soon!)**

- **Agents:**

    - **`SWE-agent`** (default): A general-purpose software engineering agent.
    - **`SWE-crafter`**: An alternative agent with different capabilities.
    - **More agents coming soon!**

## Early Stage and Feedback

🚧 **Early Access**: Issue-solver-bots is currently in the early stages of development and is considered experimental.
We are actively working to improve and expand its capabilities.

🤗 **We Value Your Feedback**: Your insights and suggestions are crucial to us.
Please share your feedback, report issues, or propose enhancements to help us make issue-solver-bots better.

## FAQ

**Q1: What permissions are required for the personal access tokens?**

- **A:** The tokens must have the necessary scopes to read and write to your repositories and access issues or pull
  requests.

**Q2: Can I use this setup with self-managed GitLab or GitHub instances?**

- **A:** Yes! Just ensure your runners are configured properly with Docker capabilities.

**Q3: How do I obtain an OpenAI API key?**

- **A:** Sign up for an API key on the [OpenAI website](https://platform.openai.com/account/api-keys).

**Q4: Is there any cost associated with using the agents?**

- **A:** Usage of certain models (like OpenAI's GPT models) may incur costs. Please refer to the respective provider's
  pricing.

**Q5: What if I need help or run into issues?**

- **A:** Feel free to reach out on our [Discord server](#community-and-support) or open an issue on GitHub.

## Community and Support

Join our community to get help, share feedback, or contribute!

[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289DA?logo=discord&logoColor=white)](https://discord.gg/wBeQhw9v)

- **Discord Server:** [Join us on Discord](https://discord.gg/wBeQhw9v)
- **GitHub Issues:** [Report issues or request features](https://github.com/umans-tech/issue-solver-bots/issues)

## Contribution

🤝 Contributions are welcome! Please refer to our [Contribution Guide](CONTRIBUTING.md) for details on how to participate
in the development of this project.

- **Bug Reports & Feature Requests:** Open an issue on
  the [GitHub repository](https://github.com/umans-tech/issue-solver-bots/issues).
- **Pull Requests:** Submit pull requests for improvements or new features.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
