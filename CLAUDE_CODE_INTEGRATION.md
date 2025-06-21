# Claude Code Integration

This document describes the integration of Anthropic's Claude Code SDK into the issue solver system.

## Overview

The Claude Code agent (`ClaudeCodeAgent`) provides advanced IDE-like capabilities for resolving code issues using Anthropic's Claude Code SDK.

## Features

- **Comprehensive Toolset**: File operations, bash commands, code analysis, and project navigation
- **IDE-like Capabilities**: Advanced code understanding and debugging features  
- **Subprocess Architecture**: Runs Claude Code as a managed subprocess
- **Web API Integration**: Available through both CLI and web API interfaces

## Installation

### Prerequisites

1. **Python Dependencies**:
   ```bash
   pip install claude-code-sdk anyio
   ```

2. **Node.js**: Claude Code SDK requires Node.js to be installed and available in PATH
   ```bash
   # Install Node.js (version 16+ recommended)
   # On macOS:
   brew install node
   
   # On Ubuntu/Debian:
   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

3. **Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

4. **Environment Variables**:
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   ```

## Usage

### CLI Usage

```bash
# Use Claude Code agent for issue resolution
python -m issue_solver solve --agent claude-code --repo-path /path/to/repo --issue "Fix the bug in authentication module"
```

### Web API Usage

```python
# Example request payload
{
    "knowledge_base_id": "kb-123",
    "issue": {
        "title": "Authentication Bug",
        "description": "Users cannot log in due to session handling issue"
    },
    "settings": {
        "agent": "claude-code",
        "max_turns": 100,
        "permission_mode": "acceptEdits"
    }
}
```

## Configuration Options

- **max_turns**: Maximum conversation turns (default: 100)
- **permission_mode**: Permission handling mode
  - `"acceptEdits"`: Automatically accept file edits
  - `"bypassPermissions"`: Bypass all permission prompts  
  - `"default"`: Use interactive mode
- **allowed_tools**: Tools available to Claude Code (default: ["Read", "Write", "Bash", "Edit"])

## Architecture

The Claude Code agent follows the existing codebase patterns:

1. **Implements `IssueResolvingAgent`**: Core interface for issue resolution
2. **Extends `CodingAgent`**: Web API compatibility interface  
3. **Factory Integration**: Available through `SupportedAgent.get()`
4. **Web API Integration**: Configured through `ResolutionSettings`

## Files Added/Modified

### New Files
- `issue-solver/src/issue_solver/agents/claude_code_agent.py`: Main agent implementation
- `issue-solver/tests/agents/test_claude_code_agent.py`: Unit tests

### Modified Files
- `issue-solver/src/issue_solver/agents/supported_agents.py`: Added to supported agents enum
- `issue-solver/src/issue_solver/webapi/dependencies.py`: Web API integration
- `issue-solver/src/issue_solver/webapi/payloads.py`: API payload definitions

## Comparison with Other Agents

| Feature | Claude Code | Anthropic Tools | SWE-Agent |
|---------|-------------|-----------------|-----------|
| **Architecture** | Subprocess SDK | Direct API | Docker Container |
| **Tool Richness** | Comprehensive IDE | Basic (bash, edit) | External Tools |
| **Setup Complexity** | Medium (Node.js) | Low | High (Docker) |
| **Customization** | Limited | High | Medium |
| **Performance** | Good | Best | Variable |

## Error Handling

The agent includes comprehensive error handling:

- **SDK Errors**: Captures and reports Claude Code SDK failures
- **Environment Issues**: Validates API key and dependencies  
- **Timeout Handling**: Manages long-running operations
- **Result Validation**: Ensures successful completion

## Logging

The agent provides detailed logging:

- Issue resolution progress
- Turn-by-turn execution details
- Success metrics (duration, cost, turns)
- Error details and stack traces

## Testing

Run the tests with:

```bash
# Run Claude Code agent tests
pytest issue-solver/tests/agents/test_claude_code_agent.py -v

# Run all agent tests
pytest issue-solver/tests/agents/ -v
```

## Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY environment variable is required"**
   - Set the `ANTHROPIC_API_KEY` environment variable
   
2. **"Node.js not found"**
   - Install Node.js and ensure it's in your PATH
   
3. **"Claude Code CLI not found"**
   - Install with `npm install -g @anthropic-ai/claude-code`
   
4. **Permission errors**
   - Check file system permissions in the repository directory
   - Ensure the agent can write to temporary directories

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Potential improvements:

- **Custom Tool Integration**: Allow custom tools beyond the default set
- **Performance Optimization**: Caching and session reuse
- **Advanced Configuration**: More granular control over Claude Code behavior
- **Monitoring Integration**: Metrics and observability features 