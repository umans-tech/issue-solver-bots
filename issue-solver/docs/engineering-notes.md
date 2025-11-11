# Engineering Notes

### Guideline: Single Behavior per Test Using Given/When/Then
- **Purpose:** Keep intent obvious and make failures actionable.
- **Explanation:** Each test narrates one behavior with explicit `# Given`, `# When`, `# Then` comments so humans and LLMs can read the story. If a scenario needs multiple When/Then pairs, split it into multiple tests instead of nesting logic.
- **Example:**
  ```python
  def test_delete_auto_documentation_prompts_should_fail_when_none_defined():
      # Given
      time_under_control.set_from_iso_format("2025-11-04T09:00:00")
      ...
      # When
      response = api_client.request("DELETE", ..., json={"promptIds": ["overview"]})
      # Then
      assert response.status_code == 404
  ```
- **Reference:** Kent Beck, *Test-Driven Development: By Example* (story-focused tests).

### Guideline: Aggregates Guard Their Own Invariants
- **Purpose:** Prevent defensive checks from leaking into controllers or workers.
- **Explanation:** Encapsulate state rules inside aggregates (e.g., `AutoDocumentationSetup.apply`). External layers hand events/commands to the aggregate and react to domain errors instead of pre-validating.
- **Example:** `AutoDocumentationSetup.apply` rejects `DocumentationPromptsRemoved` when no prompts exist, so the API doesn’t need to inspect dictionaries before emitting events.
- **Reference:** Eric Evans, *Domain-Driven Design*, Aggregates chapter.

### Guideline: Domain Exceptions Speak in Natural Language
- **Purpose:** Make failures self-explanatory in logs/tests.
- **Explanation:** Name exceptions as sentences (`CannotRemoveAutoDocumentationWithoutPrompts`) per Verraes’ “natural language message names.” The message should read like a log line humans can copy into docs.
- **Example:**
  ```python
  raise CannotRemoveUnknownAutoDocumentationPrompts(["overview"])  # -> "Cannot remove unknown auto-documentation prompts: overview"
  ```
- **Reference:** Mathias Verraes, “Messaging Patterns in Natural Language,” 2019.

### Guideline: Controllers Translate Domain Errors to Transport Codes
- **Purpose:** Keep HTTP layers declarative and thin.
- **Explanation:** FastAPI endpoints call aggregates/services and map domain exceptions to status codes (404 here). They never replicate business rules; they only translate domain outcomes into HTTP responses.
- **Example:**
  ```python
  try:
      updated_setup = auto_doc_setup.apply(event)
  except CannotRemoveUnknownAutoDocumentationPrompts as exc:
      raise HTTPException(status_code=404, detail=str(exc))
  ```
- **Reference:** Jim Weirich, “Tell, Don’t Ask” (controllers tell domains what to do, domain tells controllers the outcome).

### Guideline: Prefer Pattern Matching Over `isinstance` Chains
- **Purpose:** Improve readability when branching on domain events.
- **Explanation:** Use Python `match` statements for event-type-specific logic (statuses, aggregate mutations) instead of long `if isinstance` sequences. This makes all cases explicit and allows `assert_never` exhaustiveness checks.
- **Example:**
  ```python
  match event:
      case DocumentationPromptsRemoved(prompt_ids=prompt_ids):
          ...
      case DocumentationPromptsDefined(docs_prompts=new_prompts):
          ...
      case _:
          assert_never(event)
  ```
- **Reference:** PEP 636, *Structural Pattern Matching: Tutorial.*

### Guideline: Reuse Aggregates Across Entry Points
- **Purpose:** Keep API, workers, and CLI in sync without copy/paste.
- **Explanation:** Shared helpers like `load_auto_documentation_setup` are the single way to reconstruct state. Both HTTP handlers and background workers call them, so any rule change propagates automatically.
- **Example:** HTTP GET `/auto-documentation` and the docs-generation worker both call `load_auto_documentation_setup` to merge defined/removed events.
- **Reference:** Vaughn Vernon, *Implementing Domain-Driven Design*, on “application services delegating to domain services.”

### Guideline: Process Timelines Reflect Aggregate State, Not Latest Event Label
- **Purpose:** Present meaningful status in UI even when last event is “removal.”
- **Explanation:** When computing process status, ask the aggregate whether prompts remain. A removal event only flips the status to `removed` if the aggregate confirms no prompts left; otherwise status remains `configured` for continuity.
- **Example:** `_auto_doc_prompts_remaining()` replays events via `AutoDocumentationSetup` before returning the status string.
- **Reference:** Domain-Driven Design notion of “read models derived from aggregates,” per Greg Young’s CQRS guidance.

### Guideline: Use Natural-Language Error Messages in Tests
- **Purpose:** Ensure tests assert on human-readable intent, not opaque codes.
- **Explanation:** When expecting errors, assert substrings like "Cannot remove auto-documentation prompts" so failures remain understandable to both humans and LLMs reviewing the suite.
- **Example:** `assert "Cannot remove auto-documentation prompts" in response.json()["detail"]`
- **Reference:** Same Verraes article; also aligns with BDD-style expectation wording.

### Guideline: HTTP Test Client `request` for Verbose Methods
- **Purpose:** Avoid brittle workarounds when HTTP verbs lack helper kwargs.
- **Explanation:** Starlette’s `TestClient.delete` doesn’t accept `json`, so call `api_client.request("DELETE", ..., json=payload)` to keep tests explicit and consistent across verbs.
- **Example:** `api_client.request("DELETE", f"/repositories/{kb}/auto-documentation", json={"promptIds": [...]})`
- **Reference:** Starlette TestClient docs (method-agnostic `request`).
