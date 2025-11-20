# Auto Documentation: Stateful vs Complete Mode

Objective: add deterministic, stateful doc updates while preserving a full-regeneration option.

## Plan (incremental)
1) **Event model**: extend `DocumentationGenerationRequested` (dataclass + serializers/records) with `mode: Literal["update","complete"]`, default `update`. Backward compatibility: treat missing mode as `complete`.
2) **Request emission**: in `worker/documenting/auto.generate_docs`, set `mode="update"` for new requests; keep behavior when callers explicitly choose a mode (future API flag).
3) **Processing path**: thread `mode` through `process_documentation_generation_request` into `generate_and_load_docs`.
4) **Retrieval hook (update mode)**: before calling the agent, try to pull prior auto-generated docs for the KB (latest code_version < current). If found, hydrate the output dir with those files; otherwise fall back to from-scratch.
5) **Agent prompt**: adjust `ClaudeCodeDocsAgent` prompt to favor in-place updates (preserve headings/sections, deterministic ordering), while still working from scratch when no prior content is present.
6) **Storage/metadata**: optionally persist per-doc metadata (e.g., origin, process_id, prior_version) to aid future selective invalidation; keep existing S3 layout unchanged.
7) **Tests & fixtures**: add coverage for both modes, fallback, and continuity behavior; ensure legacy events (without mode) still process as complete.

## Test List (behaviours to cover)
- Request emission includes `mode="update"` by default; legacy flow without explicit mode still works.
- `mode="complete"` skips retrieval and generates fresh docs even if previous versions exist.
- `mode="update"` hydrates from the latest available auto-doc version; unchanged sections persist (e.g., content equality or hash match).
- `mode="update"` falls back to full generation when no prior auto docs are found.
- Legacy event (missing mode) is treated as `complete` for backward compatibility.
- Generated docs metadata remains correct (`origin=auto`, proper `process_id`, correct version path).
- Error path still records `DocumentationGenerationFailed` and does not corrupt prior docs.
