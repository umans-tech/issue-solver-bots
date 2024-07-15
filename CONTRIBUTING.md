# Contribution Guidelines

Thank you for considering contributing to issue-solver-bots! We appreciate your help in making this project better. Here are some guidelines to get you started.

## Table of Contents
1. [Getting Started](#getting-started)
2. [How to Contribute](#how-to-contribute)
   - [Reporting Issues](#reporting-issues)
   - [Submitting Pull Requests](#submitting-pull-requests)
3. [Commit Message Guidelines](#commit-message-guidelines)
4. [Templates](#templates)
5. [Code of Conduct](#code-of-conduct)
6. [License](#license)

## Getting Started

To start contributing, you need to have a GitHub account. If you don't have one, you can sign up at [GitHub](https://github.com/).

1. **Fork the repository**: Click the "Fork" button at the top right corner of this repository.
2. **Clone your forked repository**:
   ```bash
   git clone https://github.com/yourusername/issue-solver-bots.git
   cd issue-solver-bots
   ```
3. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Reporting Issues

If you encounter any bugs, issues, or have suggestions for enhancements, please feel free to [open an issue](https://github.com/umans-tech/issue-solver-bots/issues). Make sure to include as much detail as possible to help us understand and resolve the issue.

### Submitting Pull Requests

1. **Ensure your code follows the project's coding style and conventions**.
2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```
3. **Push your branch to your forked repository**:
   ```bash
   git push origin feature/your-feature-name
   ```
4. **Open a pull request**: Navigate to the original repository, click on the "Pull Requests" tab, and then click "New Pull Request". Fill out the template provided and submit your pull request.

### Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for our commit messages. Here are some examples:
- `feat: add new GitHub Actions template`
- `fix: resolve issue with GitLab CI pipeline`
- `docs: update README with new usage instructions`

Use the following types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries

### Templates

Currently, we have the following templates:

- 🛠️ **GitLab CI Template**: Automates the resolution of issues via their GitLab ID or description using SWE-agent.
- 🛠️ **GitHub Actions Template**: Automates the resolution of issues via their GitHub ID or description using SWE-agent.

**More templates and features are coming soon! 🚧**

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating in this project, you agree to abide by its terms. For more information on inclusion and diversity, refer to [Mozilla's Inclusion guidelines](https://github.com/mozilla/inclusion).

## License

By contributing to issue-solver-bots, you agree that your contributions will be licensed under the MIT License.
