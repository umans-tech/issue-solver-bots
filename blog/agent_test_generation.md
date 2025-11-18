# What's wrong with testing with agents in an existing codebases

# Test generation

- Agents struggle to generate useful tests that characterize the expected behavior of a feature/bug (less true right now)
- Agents struggle to follow the test conventions and setup in an existing codebase
- Codebase might have inconsistencies in test definition e.g. legacy and a newer more desired setup, agents might struggle to identify the desired one (this intention might not be documented)
- Tests become ever more important, as multiple agents could contribute to a codebase with plausible prs that might break existing features/behaviors or (miss/side effect of implementation??)
- Ideally tests should characterize what's the codebase is about so each gap is identified by specific failing tests that are activable to promptly identify the gap
- Codex thrives with tdd
- codebase capabilities to ease verifiability 

# Examples
- fixture not used, hard coding stuff
- introducing  complex concepts that were never present in the codebase

# Ideas

- migrate tests and tests uncovered codebase part
- context rot skills can help with it
- verify what the agent does
- reward hacking

# What worked for us
- testing from agent doesn't respect implicit rule in our testing
- good faith starting point and finding it complex to test the right behavior so end up mocking everything and the test end up being no useful and not testing the right behavior
- first red test as a starting point, then iterating over it
- spikes for missing knowledge

# experimentation setup

- [x] playwright screenshot can be showed? 
- [ ] install codex and repo perquisites on morph
- [ ] expose ports opened on morph


# show screenshot and video

config codex below and the screenshots will found in output_dir

[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest",
        "--output-dir=/Users/naji/Documents/Projects/tutor/swe-agent/issue-solver-bots/blog/outputs",
        "--save-trace",
        "--save-video=1280x720"]



- storybook