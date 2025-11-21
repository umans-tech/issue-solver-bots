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
