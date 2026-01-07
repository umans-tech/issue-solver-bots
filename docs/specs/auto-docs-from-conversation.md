# Auto Documentation — Publish From Conversation (Proposed)

Status: Proposed (not yet implemented)
Last updated: 2026-01-02

## 1) Summary

This feature allows a user to turn an approved chat output into an auto-doc that appears in the Docs tab immediately, while also configuring the prompt so future indexing regenerates it. This is a new capability and is not implemented yet.

## 2) User Requirements (Confirmed)

- Requires a connected repo (knowledge base).
- Prompt description is inferred from the conversation by the model.
- Doc paths can include folders (simple `/` support).
- No new process type; publish directly into the latest auto-doc version and define prompt for next indexing.

## 3) Proposed Flow

1) User asks in chat: “Turn this into auto documentation.”
2) UI triggers a publish action for a specific assistant message.
3) The model infers a prompt description from the conversation and output.
4) Backend writes the doc to the latest indexed commit and registers the prompt.
5) The doc appears in Docs tab as an auto doc and updates on next indexing.

## 4) Backend Design (Proposed)

### 4.1 Endpoint
`POST /repositories/{knowledge_base_id}/auto-documentation/publish`

Payload (proposed):
- `path` (string) — e.g., `architecture/overview.md`
- `title` (string)
- `content` (markdown)
- `inferred_prompt` (string)
- `chat_id` (string)
- `message_id` (string)

Behavior:
- Validate repo connection exists.
- Require latest indexed commit (otherwise return 409).
- Define/overwrite prompt mapping via `DocumentationPromptsDefined`.
- Write doc to S3 under latest commit with metadata:
  - `origin: auto`
  - `source: conversation`
  - `chat_id`, `message_id`
- Return doc path + commit.

### 4.2 Prompt ID Strategy
- Prompt ID derived from doc path (without `.md`).
- Example: `architecture/overview`.

## 5) Frontend Design (Proposed)

### 5.1 Chat UI
- Add “Publish to Docs” action on assistant messages.
- Collect path/title from user.
- Infer prompt description using the model.
- Submit to backend publish endpoint.

### 5.2 Next API Route
`POST /api/docs/publish`
- Authenticated; forwards to backend publish endpoint.

## 6) Validation & Edge Cases

- Missing repo connection → 404.
- No indexed commit → 409.
- Empty content → 400.
- Invalid path → 400 (must be non-empty; allow `/`).
- Existing file at path → decide whether to overwrite (TBD).

## 7) Open Questions

- Should the prompt inference be visible/editable before save?
- Should publishing overwrite existing doc paths, or fail with 409?
- Should the publish action emit any existing doc generation events, or only write directly to S3?

---

Implementation status: **Not implemented**. This spec is for iteration.
