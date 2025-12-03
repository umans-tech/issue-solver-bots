---
title: "Can coding agents actually follow your codebase’s rules?"
publishDate: 2025-11-29
excerpt: "We ran a reality check to see how well different coding agents follow a repo’s AGENTS.md in practice."
isFeatured: true
seo:
  title: "Do coding agents follow AGENTS.md?"
  description: "A practical experiment measuring how closely various coding agents obey repository rules when writing tests."
  image:
    src: "../../assets/images/experimentation_setup.jpeg"
    alt: "Experimentation setup"


---

Benchmarks say instruction following is getting better.
Day to day, it often doesn’t feel that way.

This article is about a small reality check we ran:

> Given a real module and a clear `AGENTS.md`,
> how well do different agents actually follow the rules of the repo when they work on it?

The short version of what we found:

* Even with a detailed `AGENTS.md`, frontier models still ignore or bend important repo rules in practice.
* The same models behaved more responsibly in their provider-native tools, OpenAI’s GPT-5.1 Codex-Max via Codex CLI, Anthropic’s Claude Sonnet 4.5 via Claude Code, than in Cursor, which often felt more like “raw generation” than an agent operating inside the repo.
* Strong models are very good at pushing the numbers that are easy to see, coverage, number of tests, matching comments, but they still struggle to stay focused on the behaviors that actually matter in the codebase.

<!-- Looks promising, moves the challenge somewhere else. it's more a small conclusion here -->

## Why we did this

In the first [article](https://blog.umans.ai/blog/consistency-matters/), we argued that consistency in a codebase comes from a human loop: decide → record → apply. Agents don’t automatically join that loop just because they can see your code. Unless you give them explicit, repo-local rules and checks to latch onto, they tend to optimize for “get this change done” and let small deviations from the conventions accumulate.

So in this experiment, we tried to do a bit better than that:

* we gave agents a concrete contract inside the repo (`AGENTS.md`),
* we ran them as actual coding agents (editing files, running commands),
* and we checked how closely their behavior matched what we asked for.

In parallel, labs keep announcing [“improved instruction following”](https://openai.com/index/gpt-5-1/), but most of the popular instruction-following benchmarks (e.g. [IFEVAL](https://arxiv.org/abs/2311.07911) and [COLLIE](https://collie-benchmark.github.io/)) are already essentially maxed (see [o3-mini](https://openai.com/index/gpt-4-1/) for IFEVAL and [GPT-5](https://openai.com/index/introducing-gpt-5/) for COLLIE) out for top models. Those numbers don’t tell you whether a model will respect three pages of project-specific rules once it is inside your repository.

We wanted a small, concrete check anchored in reality:

* one real module,
* one real `AGENTS.md` (and a `CLAUDE.md` copy for Claude Code, which expects that filename),
* a few different agent setups,
* and a clear question: 
> **how well do they follow the rules when they work on real files, end to end?**

This is a small, opinionated experiment on one codebase and one kind of task. It is here to make our own day-to-day experience with agents a bit more concrete and comparable, not to claim any universal ranking of models or tools.

## Goals of the experiment

<!--  as a proxy to see how likely they can follow conventions-->

We scoped the experiment around four goals.

1. Measure *agentic* instruction following inside a codebase
   Instead of looking at isolated prompts, we focused on how agents behave over a small run in the repo: reading `AGENTS.md`, editing files, running commands, and then seeing how faithfully their overall behavior matches the repo rules, as a proxy for how likely they are to follow conventions in real work.

2. Test the `AGENTS.md` approach
   Inspired by the [agents.md](https://agents.md/) initiative, we maintain an `AGENTS.md` file that explains how to work in the project so we don’t have to repeat ourselves in every prompt. For Claude Code, we expose the same content via `CLAUDE.md`.
   This experiment asks:

   * do agents actually use it when it is available?
   * which parts of it do they respect (testing style, comments, fixtures, running checks)?
   * which parts do they ignore?

3. Compare models *and* scaffoldings
   We wanted to see not just “which model is best?”, but:

   * how the same models behave in provider-native tools (Codex CLI for GPT-5.1 Codex-Max, Claude Code for Sonnet/Opus 4.5 and Gemini-CLI for Gemini 3 Pro),
   * versus the same models running as agents in Cursor.
     In other words: does the surrounding scaffolding change how seriously they take repo rules and checks?

4. Start with tests, where we can verify things
   We chose tests as the first domain because:

   * they are easy to run automatically,
   * we can define simple repo-specific heuristics (Given/When/Then comments, fixture reuse, coverage),
   * and we can ask another model to review the generated tests for more qualitative issues.

   Test generation also has a growing body of work. Benchmarks like [SWT-bench](https://swtbench.com/?results=verified) measure whether generated tests can distinguish correct patches from broken ones. We wanted to see something different: not just whether tests *work*, but whether agents follow the structural and stylistic rules the repo asks for.

Next, we’ll look at how we set the experiment up, what actually happened, and what we changed in how we use these agents as a result.

## Experiment setup

<iframe
  src="/blog/process_diagram.html"
  style="width: 100%; max-width: 100%; height: 400px; border: none; background: transparent; display: block; margin: 0 auto;"
  loading="lazy"
></iframe>
<figcaption style="text-align: center; font-size: 0.9em; color: #666;">
    Experiment pipeline: task → agent run → quality evaluation
</figcaption>

The diagram above is basically the whole experiment:
**give a task → let an agent work in the repo → analyse the tests it wrote.**

### Task and codebase

We run everything inside a real repository.
Agents can see the whole codebase, but we focus the task on one module:

* `bash.py` - 143 lines
* `edit.py` - 288 lines

So the target surface is **431 lines of code**.

Every run gets the same instruction:

> Add tests for this module, following the existing testing style and guidelines.

The repo already contains:

* an `AGENTS.md` with testing rules (and a `CLAUDE.md` copy for Claude Code),
* existing fixtures in `tests/conftest.py`,
* the rest of the project code, which the agent is free to inspect.

### Agent configurations

We try several "model + tool" setups on exactly the same repo snapshot:

* GPT-5.1 Codex-Max via **Codex CLI** (high and extra-high effort)
* GPT-5.1 Codex via **Codex CLI** (high effort)
* Claude Sonnet 4.5 and Opus 4.5 in **Claude Code** (Thinking)
* Gemini 3 Pro via **Gemini CLI**
* Claude Sonnet 4.5 in **Cursor** (Thinking)
* Gemini 3 Pro in **Cursor** (High)
* GPT-5.1 Codex High in **Cursor**

The precise flags and prompts live in the appendix; the important bit is that only the agent setup changes, not the task or the repo.

### Run pipeline

For each configuration we follow the same steps:

1. **Fresh workspace**
   Create a clean clone of the repo for that agent.

2. **Agent run**
   Start the agent once, non-interactively. It can read `AGENTS.md`, browse the codebase, edit tests, and run commands until it decides the task is done.

3. **Collect tests**
   From all its edits, we keep only the new or modified tests related to `bash.py` and `edit.py`.

4. **Automatic checks**
   Run our usual project checks on those tests.
   If something fails, we feed the error output back to the same agent once, let it fix things, and rerun the checks.

5. **Evaluation**
   On the final tests, we measure:

   * whether they pass,
   * how much of `bash.py` and `edit.py` they cover,
   * whether they follow the visible parts of the style (Given/When/Then comments, fixtures, pytest),
   * and how they look under a quick human + model review against `AGENTS.md`.

The next section looks at how the different setups behaved under this pipeline, and which ones produced tests we would actually want to keep.

## Results

At a high level, three things stood out:

* Agents running in **provider tools** (Codex CLI, Claude Code) behaved more like collaborators inside the repo: they respected more of `AGENTS.md`, ran checks, and produced code we could imagine keeping after edits.
* The Cursor and Gemini CLI setups were weaker on convention-following: they produced working tests but ignored style rules like Given/When/Then comments and fixture 
  centralization. Cursor agents, specifically, needed an external loop to rescue them with error output and checks.
* None of the setups fully matched the testing style in `AGENTS.md`; every one drifted somewhere (missing behaviors or formatting, ignoring fixtures, or over-focusing on internals).

<iframe
  src="/blog/metrics_chart.html"
  style="width: 100%; max-width: 100%; height: 800px; border: none; background: transparent; display: block; margin: 0 auto;"
  loading="lazy"
></iframe>
<figcaption style="text-align: center; font-size: 0.9em; color: #666;">
  Agent comparison across five quality dimensions
</figcaption>

**Radar chart legend:**
* **Coverage**: percentage of the target module (431 LOC) exercised by tests
* **Formatted**: percentage of tests using `# Given` / `# When` / `# Then` comments
* **Factored**: percentage of fixtures centralized in `conftest.py` (vs. defined locally)
* **Behavioral**: percentage of tests asserting on outputs rather than internals
* **Concise**: inverse of test LOC per coverage point (more coverage with fewer lines = higher score)



### Codex CLI (GPT-5.1 Codex-Max and Codex)

We ran three configurations: Codex-Max at **extra-high** and **high** effort, plus GPT-5.1 Codex at **high** effort.

All three runs were the most "balanced" in this experiment:

* small, readable tests with `# Given` / `# When` / `# Then` comments,
* checks passed on first run without needing an external loop,
* coverage in the **high 70s to low 80s** range.

Codex-Max (high) was the **only configuration** that created a `conftest.py` at all. It centralized one of its three fixtures there; the other two were still defined locally. Every other setup ignored the fixture centralization rule entirely.

The main gap was depth: core flows were covered, but several edge conditions and error paths remained untested.

### Claude Code (Sonnet 4.5 and Opus 4.5, with Thinking)

Both Claude models ran with **Thinking mode** enabled.

**Sonnet 4.5** produced the highest coverage (**96.8%**) but also the largest diff (57 tests, 936 LOC). It:

* followed the visible style very strongly (pytest, `# Given` / `# When` / `# Then`, fixtures),
* always finished with checks green,
* but generated many assertions tied to internal details, not just behavior.

**Opus 4.5** was similar in character (46 tests, 95% coverage) but with slightly fewer implementation-coupled assertions.

Both would work best as a **map of scenarios and edge cases** rather than something to merge directly.

### Gemini CLI (Gemini 3 Pro)

Gemini 3 Pro through Gemini CLI landed at **89% coverage** with 28 tests, a reasonable middle ground.

However, it completely ignored the `# Given` / `# When` / `# Then` comment style (0% compliance) and did not centralize fixtures. Tests were structured as flat functions without class organization. In a real PR, the raw logic could be useful, but the tests would need reformatting to match project conventions.

### Cursor (Sonnet 4.5, Gemini 3 Pro, Codex High)

All three Cursor configurations shared the same pattern: strong on paper, but needing heavy curation.

* **Sonnet 4.5 (Thinking)**: 90.7% coverage, 45 tests. Used G/W/T comments, but never reused fixtures and relied on the outer loop to fix failing checks.

* **Gemini 3 Pro (High)**: 90.8% coverage, 21 tests. Ignored G/W/T entirely, no fixture reuse, and did not run project checks by itself.

* **Codex High**: Only 55% coverage with 4 tests. Matched the surface style but leaned heavily on mocks instead of exercising real behavior.

Across all Cursor setups, agents did not self-verify with the project's quality guardrail. In a real PR, we would mostly skim these for ideas and then rewrite.

## What we learned

From this single module and task, three things stood out.

1. **`AGENTS.md` is a good start, not a full solution**

   Having a repo-local contract (`AGENTS.md` / `CLAUDE.md`) is clearly better than re-explaining everything in each prompt. It makes expectations visible and reusable.

   But even with that in place:

   * some setups ignored parts of the testing style (Given/When/Then, fixtures),
   * some did not self-verify with the quality guardrail before finishing,
   * some reached high coverage in a shape we wouldn't merge.

   So `AGENTS.md` is a useful baseline, not a guarantee that agents will behave the way you intend.

2. **Good models can be held back by their scaffolding**

   In this experiment, the same underlying models behaved differently depending on where they ran:

   * GPT-5.1 Codex-Max in Codex CLI and Claude Sonnet 4.5 in Claude Code respected more of `AGENTS.md` and consistently finished with working code.
   * The Cursor agents (Gemini 3 Pro, Sonnet 4.5, Codex High) only partially followed the guidelines and relied on an external loop to run checks and feed back errors.

   The point is not that scaffolding is “as important” as the model, but that a good model inside a weak or misaligned wrapper can feel much less useful than it should. We have to evaluate the **model + agent + tooling** together.

3. **Fixture reuse and centralization is where agents struggled the most**

   Benchmarks like [SWT-bench](https://swtbench.com/?results=verified) show that frontier models can already produce behavioral tests that characterize code well enough to distinguish correct patches from broken ones. In our experiment, most agents also achieved high "behavioral" scores, asserting on outputs rather than internals.

   The harder target turned out to be the **structural** requirement in `AGENTS.md`: centralizing fixtures in `conftest.py` and reusing existing helpers instead of creating bespoke setup in each test file.

   Only one configuration (Codex-Max, high effort) even created a `conftest.py`, and it only centralized one of its three fixtures there. Every other agent:

   * defined fixtures locally in each test file,
   * duplicated setup code across tests,
   * or ignored fixtures entirely.

   This matters because scattered fixtures accumulate maintenance debt and make it harder to evolve the codebase without breaking tests. The explicit rule was there and agents just didn't follow it.

## What's next

This experiment is a first small step on the apply side of the previous [article](https://blog.umans.ai/blog/consistency-matters/): taking the conventions we have written down and watching how coding agents behave against them in a live repo. One thing it suggests is that when even a small part of those expectations becomes an executable check, agents can lean on it instead of guessing and the same signal that guides them also gives human teams a clearer view of when code is drifting from the conventions they care about.

From here, the plan is to keep exploring in that direction with small, concrete experiments, looking for ways to turn more of a codebase's intent into this kind of actionable feedback.


## Appendix - detailed results

All numbers below are for the same target: the 431 lines of `bash.py` (143 LOC) and `edit.py` (288 LOC), after at most one automatic “run checks → feed errors back once” loop.

| Metric | Opus 4.5 | Sonnet 4.5 | Sonnet 4.5 (Cursor) | Gemini 3 Pro | Gemini 3 Pro (Cursor) | Codex-Max (xhigh) | Codex-Max (high) | Codex (high) | Codex (Cursor) |
|--------|-----------------|---------------|-------------------|--------------|---------------------|-------------------|------------------|--------------|--------------|
| **Scaffolding** | Claude Code | Claude Code | Cursor | Gemini CLI | Cursor | Codex CLI | Codex CLI | Codex CLI | Cursor |
| **Total Tests** | 46 | 57 | 45 | 28 | 21 | 10 | 6 | 10 | 4 |
| **LOC Written** | 582 | 936 | 769 | 274 | 260 | 197 | 125 | 194 | 110 |
| **Coverage** | 95.1% | 96.8% | 90.5% | 89.4% | 90.5% | 82.3% | 75.0% | 78.6% | 54.1% |
| **GWT** | 98% | 100% | 100% | 0% | 0% | 100% | 100% | 100% | 100% |
| **Behavioral** | 84.8% | 82.5% | 100% | 92.9% | 100% | 100% | 100% | 90% | 100% |
| **Factored** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 1/3 | ❌ | ❌ |


### `AGENTS.md` - Testing guidelines

``` markdown
- Make tests read like short stories of real usage; assert externally visible behaviour, not internal logging or strings that may change.
- Comment only with `# Given`, `# When`, `# Then`; let fixture and helper names explain the setup.
- Centralize fixtures in `tests/**/conftest.py`; build small, realistic fixtures per domain (e.g., minimal filesystem, HTTP payload, queue event) instead of bespoke per-test setup.
- Keep tests fast and deterministic: tighten timeouts when you need one, avoid sleeps, and prefer parametrization over copy‑paste cases.
- Target behaviours that matter to users—successful flows and a few critical failures that change the experience—rather than defensive checks that don’t surface externally.
- Use behavioural assertions (state changed, side effect happened, command allowed/denied) so alternative implementations that keep behaviour intact stay green.
- Quality guardrail is the alias chain `just l c f t` (ruff lint → mypy → ruff format → pytest).
- Tests should mirror existing behavioural suites like `tests/events/test_auto_documentation.py` and `tests/queueing/test_sqs_queueing_event_store.py`—fixtures plus Given/When/Then assertions.

```
