# Auto Documentation: Stateful vs Complete Mode

Objective: add deterministic, stateful doc updates while preserving a full-regeneration option.

## Plan (incremental)
1) **Event model**: keep `mode: Literal["update","complete"]`, default `update`; backward compatibility—missing mode acts as `complete`.
2) **Request emission**: emit `mode="update"` in `generate_docs`; allow callers to override to `complete`.
3) **Processing path**: thread mode through processing; keep one codepath with a single branching guard.
4) **Retrieval hook (update mode)**: find the latest `DocumentationGenerationCompleted` for the KB (different code_version); seed those auto docs into the output dir; if none, run fresh.
5) **Agent prompt**: nudge for in-place updates while deterministic.
6) **Tests**: cover default update emission, update seeding via last completion, complete mode skipping seed, legacy/missing mode defaulting to complete, and failure path integrity.

## Test List (behaviours to cover)
- Request emission uses `mode="update"` by default; legacy events still process.
- `mode="update"` pulls last completed version for the KB and seeds auto docs (when prompt unchanged).
- `mode="complete"` skips seeding even if prior auto docs exist.
- Missing mode defaults to `complete`.
- Generated docs keep metadata (`origin=auto`, process_id, version path).
- Failure path still records `DocumentationGenerationFailed` without altering prior docs.
