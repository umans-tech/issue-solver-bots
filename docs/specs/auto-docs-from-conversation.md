# Auto Documentation — Publish From Conversation

Status: Current (implemented)
Last updated: 2026-01-07

## 1) Summary

This feature allows a user to turn an approved chat output into an auto-doc that appears in the Docs tab immediately, while also configuring the prompt so future indexing regenerates it.

## 2) User Requirements (Confirmed)

- Requires a connected repo (knowledge base).
- Prompt description is inferred from the conversation by the model.
- Doc paths can include folders (simple `/` support).
- No new process type; publish directly into the latest auto-doc version and define prompt for next indexing.

## 3) Flow

1) User asks in chat: “Turn this into auto documentation.”
2) The assistant calls `publishAutoDoc` for the approved output.
3) The model infers a prompt description from the conversation and output.
4) The tool fetches the latest indexed commit and registers the prompt.
5) The tool writes the doc to S3 with auto metadata and records a completed generation event.
6) The doc appears in Docs tab as an auto doc and updates on next indexing.

## 4) Backend Design

### 4.1 Endpoints Used

- `GET /repositories/{knowledge_base_id}/auto-documentation/latest-indexed-commit`
- `POST /repositories/{knowledge_base_id}/auto-documentation` (existing prompt config)
- `POST /repositories/{knowledge_base_id}/auto-documentation/publish-completed`

Behavior:
- Validate repo connection exists.
- Require latest indexed commit (otherwise return 409).
- Define/overwrite prompt mapping via `DocumentationPromptsDefined`.
- Record a `DocumentationGenerationCompleted` event for the prompt and commit.

### 4.2 Prompt ID Strategy
- Prompt ID derived from doc path (without `.md`).
- Example: `architecture/overview`.

## 5) Frontend Design

### 5.1 Chat UI
- The assistant uses the `publishAutoDoc` tool when the user asks to publish.
- Tool inputs include `title`, `path`, `content`, and `promptDescription`.
- Path supports folders and is normalized to a `.md` file.

### 5.2 Storage
- The tool writes the markdown file directly to S3 under the latest commit.
- Metadata is updated in `__metadata__.json` with:
  - `origin: auto`
  - `source: conversation`
  - `process_id`
  - `chat_id`, `message_id` (if provided)

## 6) Validation & Edge Cases

- Missing repo connection → 404.
- No indexed commit → 409.
- Empty content → 400.
- Invalid path → 400 (must be non-empty; allow `/`).
- Existing file at path → overwrite (new content becomes the latest auto doc for that path).

## 7) Future Enhancements

- Allow preview/edit of inferred prompt before publishing.
- Add a manual “Publish to Docs” button for assistant messages.
