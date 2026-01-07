# Auto Documentation — Current System

Status: Current
Last updated: 2026-01-02

## 1) Summary

Umans supports automatic documentation generated from code via prompt definitions stored in the backend. Docs are produced by a worker pipeline, stored in S3, and displayed in the Docs tab. This spec documents the current behavior only.

## 2) Scope

- Auto-doc prompt configuration
- Doc generation workflow on indexing
- Manual doc generation
- Storage format and metadata

## 3) Current Behavior

### 3.1 Prompt Configuration (Backend)

- Prompt definitions are event-sourced with:
  - `DocumentationPromptsDefined`
  - `DocumentationPromptsRemoved`
- Prompts are loaded via `load_auto_documentation_setup` and represent the latest configuration for a knowledge base.

### 3.2 Generation Flow (Worker)

- On `CodeRepositoryIndexed`, the worker emits `DocumentationGenerationRequested` for each prompt (mode `update`).
- On `DocumentationGenerationRequested`, the worker:
  1) Clones the repo at the target commit.
  2) Seeds previous auto-docs (when mode is `update`).
  3) Runs the docs agent to generate markdown files.
  4) Stores generated docs in S3.
  5) Emits `DocumentationGenerationCompleted`.

### 3.3 Manual Generation (Backend)

- `POST /repositories/{knowledge_base_id}/auto-documentation/generate`
  - Validates prompt exists.
  - Requires the repo to be indexed.
  - Emits `DocumentationGenerationRequested`.

### 3.4 Storage Format (S3)

- Docs are stored under:
  - `base/{knowledge_base_id}/docs/{commit_sha}/...`
- Metadata is stored in:
  - `__metadata__.json`
- Auto-docs are marked with `origin: auto`.

### 3.5 Docs UI

- Docs tab lists files from S3 and uses metadata to display origin and approvals.
- Doc prompts can be configured via the Docs Setup panel.

## 4) Key Paths (Reference)

Backend:
- `src/issue_solver/events/auto_documentation.py`
- `src/issue_solver/worker/documenting/auto.py`
- `src/issue_solver/worker/documenting/s3_knowledge_repository.py`
- `src/issue_solver/webapi/routers/repository.py`

Frontend:
- `app/docs/[spaceId]/[[...path]]/page.tsx`
- `components/doc-prompts-panel.tsx`
- `app/api/docs/*` routes
