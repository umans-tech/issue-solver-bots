# Contributing to `issue-solver`

These are the working guidelines we’ve been using in this codebase. They are intentionally concise so you can scan and
apply them quickly.

## Run tests, don’t speculate

Let tests drive changes instead of defensive code.

### Why:

Prevents dead code and catches regressions early.

### How:

Run the smallest relevant scope (`uv run -m pytest tests/<area>`). Expand only if needed.

### Example:

When tweaking the config parser, run `uv run -m pytest tests/config/` rather than skipping tests or running the whole
suite.

## Narrow tests to intent

Test the smallest behavior that proves the point.

### Why:

Focused tests are stable and pinpoint failures.

### How:

Prefer unit/serialization tests over full pipelines when checking defaults or small transforms.

### Example:

To verify a JSON record defaults `status` to `"draft"` when missing, build the record JSON and assert the field—don’t
start the web server or hit storage.

## Prefer simpler control flow

Fewer branches, clearer paths.

### Why:

Less cognitive load and fewer bugs.

### How:

Use early returns; drop redundant conditions.

### Example:

Replace nested `if user` + `if user.active` with:

  ```python
  if not user or not user.active:
    return None
return user.name
  ```

## Name for the context, not the caller

Types describe what they are, not how a caller uses them.

### Why:

Keeps models reusable and readable.

### How:

Use neutral names (`DocRef`), encode “previous/next/current” in variable names at call sites.

### Example:

`DocRef` + `previous_doc: DocRef` instead of defining `PreviousDocRef`.

## Single-responsibility helpers

Each helper does one thing at one abstraction level.

### Why:

Easier to test, reuse, and change safely.

### How:

Split flows into validation, persistence, side-effects instead of one mega-function.

### Example:

`validate_signup()`, `persist_user()`, and `send_welcome_email()` instead of one `create_user()` that does all three
inline.

## Type consistency

Use precise types; avoid redundant existence checks.

### Why:

Reduces runtime surprises and noisy guards.

### How:

Prefer `Literal`/`Enum`/typed dataclasses to bare strings; don’t `hasattr` fields that always exist.

### Example:

`Status = Literal["draft", "published"]` with `status: Status`; remove `if hasattr(obj, "status")`.

## Keep logging/telemetry purposeful

Log decisions, not noise.

### Why:

Helps ops/debugging without drowning signals.

### How:

Log key choices and outcomes (inputs, selected path, result), skip repetitive “starting/ending” chatter.

### Example:

On retry, log `{order_id, attempt, backoff_ms, reason}` once; avoid per-loop “still retrying” spam.

## Repo-specific conventions

### Tests read like docs
Use `# Given`, `# When`, `# Then` sections; lean on fixtures and personas (e.g., `BriceDeNice`) instead of ad-hoc setup.

**Why:** Keeps intent obvious and failures self-explanatory.

**How:** Structure test bodies with the three sections; prefer shared fixtures/personas to inline setup.

**Example:**
```
# Given
process_id = BriceDeNice.first_repo_integration_process_id()
# When
await run_index_repository(settings, deps)
# Then
assert ...
```

### Prefer explicit dependencies over monkeypatch
Inject collaborators (often ABC-backed) and use `Mock(spec=RealType)` or simple fakes; avoid `monkeypatch` when a dependency can be passed.

**Why:** Reduces hidden coupling and keeps tests deterministic.

**How:** Add a dependency object/fixture and pass it; use `Mock(spec=Type)` to catch API drift.

**Example:**
```
deps = Dependencies(event_store=InMemoryEventStore(), git_helper=Mock(spec=GitHelper), indexer=Mock(spec=RepositoryIndexer))
await run_index_repository(settings, deps)
```

### Keep collaborators at the right boundary
Add small ABCs in domain packages (e.g., `indexing/repository_indexer`) and pass them through dependency objects for clarity and testability.

**Why:** Makes responsibilities explicit and swappable without monkeypatching internals.

**How:** Define a minimal ABC near the domain, inject it via a dependencies object, and implement/compose it in production code.

**Example:** `RepositoryIndexer` with `upload_full_repository` and `apply_delta` methods, injected into the CLI command.

### CLI subcommands stay consistent
Add via `CliApp.run`, mention in the `cudu` usage text, and keep flags minimal and intent-revealing.

**Why:** Users get a predictable interface; code paths stay uniform.

**How:** Register the subcommand in `cudu_cli.py`, update `show_usage()`, and avoid redundant flags (infer when possible).

**Example:** `index-repository` wired with `CliApp.run(..., cli_cmd_method_name="cli_cmd")` and documented in usage.

### Clocks are injected
Prefer an injected `Clock` over direct system time (e.g., `datetime.now()` / `UTCSystemClock()` inline).

**Why:** Time-sensitive code stays testable and avoids “time bombs” from real clocks; ties to the consistency themes in `blog/src/content/blog/consistency-matters.md`.

**How:** Add a `clock` to dependency objects and use `clock.now()`; in tests, pass `ControllableClock` or a `Mock(spec=Clock)`.

**Example:**
```
deps = Dependencies(event_store=store, git_helper=git, indexer=indexer, clock=ControllableClock(fixed_time))
await deps.event_store.append(process_id, SomeEvent(occurred_at=deps.clock.now(), ...))
```

### Dependency injection over patching
Expose collaborators (clocks, indexers, clients, etc.) via dependency objects or constructors; avoid monkeypatching module globals in tests.

**Why:** Keeps coupling explicit, reduces hidden state, and makes tests deterministic.

**How:** Pass mocks/fakes through dependency objects or initializer parameters; define small ABC-backed interfaces (e.g., `RepositoryIndexer`) and inject them.

**Example:**
```
deps = IndexRepositoryDependencies(event_store=store, git_helper=git, indexer=Mock(spec=RepositoryIndexer), clock=fixed_clock)
await run_index_repository(settings, deps)
```
