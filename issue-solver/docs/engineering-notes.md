# Engineering Notes


### Guideline: Describe One Behavior per Test Using Given / When / Then
- **Purpose:** Keep intent obvious and make failures actionable.
- **Explanation:** Each test narrates exactly one behavior, annotated with `# Given`, `# When`, `# Then` comments. If the scenario needs multiple When/Then blocks, extract additional tests instead of branching. This helps humans and LLMs understand failures immediately.
- **Example:**
  ```python
  def test_delete_auto_documentation_prompts_should_fail_when_none_defined(
      api_client,
      time_under_control,
  ):
      # Given
      time_under_control.set_from_iso_format("2025-11-04T09:00:00")
      ...
      # When
      response = api_client.request(
          "DELETE",
          f"/repositories/{knowledge_base_id}/auto-documentation",
          json={"promptIds": ["overview"]},
      )
      # Then
      assert response.status_code == 404
  ```
- **References:**
  - Kent Beck, *Test-Driven Development: By Example* ([Addison-Wesley](https://www.informit.com/store/test-driven-development-by-example-9780321146533)).
  - Dan North, “Introducing BDD,” 2006 ([dannorth.net](https://dannorth.net/introducing-bdd/)).

### Guideline: Use Aggregates as the Source of Truth
- **Purpose:** Encapsulate invariants and state transitions in one place.
- **Explanation:** Aggregates (e.g., `AutoDocumentationSetup`) rehydrate themselves from events and enforce rules in `apply()`. External layers don’t manipulate raw state; they hand commands/events to the aggregate and react to the outcome. This prevents defensive checks from leaking into controllers or workers.
- **Example:** `AutoDocumentationSetup.apply()` raises `CannotRemoveAutoDocumentationWithoutPrompts` if a removal event arrives before any definition, so no caller needs to pre-check for prompt existence.
- **References:**
  - Eric Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software* ([Addison-Wesley](https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-of-9780321125217)).
  - Vaughn Vernon, *Implementing Domain-Driven Design* ([Addison-Wesley](https://www.informit.com/store/implementing-domain-driven-design-9780321834577)).

### Guideline: Domain Exceptions Speak in Natural Language
- **Purpose:** Make failures self-explanatory in logs/tests.
- **Explanation:** Name exceptions as sentences (`CannotRemoveAutoDocumentationWithoutPrompts`) per Verraes’ “natural language message names.” The message should read like a log line humans can copy into docs.
- **Example:**
  ```python
  raise CannotRemoveUnknownAutoDocumentationPrompts(["overview"])  # -> "Cannot remove unknown auto-documentation prompts: overview"
  ```
- **References:**
  - Mathias Verraes, “Messaging Patterns in Natural Language,” 2019 ([verraes.net](https://verraes.net/2019/06/messaging-patterns-natural-language-message-names/)).
  - Eric Evans, *Domain-Driven Design* (Ubiquitous Language chapter).

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
- **References:**
  - Jim Weirich, “Tell, Don’t Ask,” RubyConf 2009 talk ([YouTube](https://www.youtube.com/watch?v=TOG1nEtFxQ0)).
  - Mark Richards & Neal Ford, *Fundamentals of Software Architecture* (Chapter on Architecture Characteristics).

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
- **References:**
  - PEP 636 – *Structural Pattern Matching: Tutorial* ([python.org](https://peps.python.org/pep-0636/)).
  - Brett Cannon, “Structural Pattern Matching in Python 3.10,” 2021 ([devblogs.microsoft.com](https://devblogs.microsoft.com/python/python-3-10-is-here/)).

### Guideline: Reuse Aggregates Across Entry Points
- **Purpose:** Keep API, workers, and CLI in sync without copy/paste.
- **Explanation:** Shared helpers like `load_auto_documentation_setup` are the single way to reconstruct state. Both HTTP handlers and background workers call them, so any rule change propagates automatically.
- **Example:** HTTP GET `/auto-documentation` and the docs-generation worker both call `load_auto_documentation_setup` to merge defined/removed events.
- **References:**
  - Vaughn Vernon, *Implementing Domain-Driven Design* ([Addison-Wesley](https://www.informit.com/store/implementing-domain-driven-design-9780321834577)).
  - Greg Young, “CQRS and Event Sourcing” ([infoq.com](https://www.infoq.com/articles/cqrs-event-sourcing/)).

### Guideline: Process Timelines Reflect Aggregate State, Not Latest Event Label
- **Purpose:** Present meaningful status in UI even when last event is “removal.”
- **Explanation:** When computing process status, ask the aggregate whether prompts remain. A removal event only flips the status to `removed` if the aggregate confirms no prompts left; otherwise status remains `configured` for continuity.
- **Example:** `_auto_doc_prompts_remaining()` replays events via `AutoDocumentationSetup` before returning the status string.
- **References:**
  - Greg Young, “CQRS and Event Sourcing” ([infoq.com](https://www.infoq.com/articles/cqrs-event-sourcing/)).
  - Udi Dahan, “CQRS and Why You Need It,” 2010 ([udidahan.com](https://udidahan.com/2010/02/02/cqrs-and-why-you-need-it/)).

### Guideline: Use Natural-Language Error Messages in Tests
- **Purpose:** Ensure tests assert on human-readable intent, not opaque codes.
- **Explanation:** When expecting errors, assert substrings like "Cannot remove auto-documentation prompts" so failures remain understandable to both humans and LLMs reviewing the suite.
- **Example:** `assert "Cannot remove auto-documentation prompts" in response.json()["detail"]`
- **References:**
  - Mathias Verraes, “Messaging Patterns in Natural Language,” 2019 ([verraes.net](https://verraes.net/2019/06/messaging-patterns-natural-language-message-names/)).
  - Dan North, “Introducing BDD,” 2006 ([dannorth.net](https://dannorth.net/introducing-bdd/)).

### Guideline: HTTP Test Client `request` for Verbose Methods
- **Purpose:** Avoid brittle workarounds when HTTP verbs lack helper kwargs.
- **Explanation:** Starlette’s `TestClient.delete` doesn’t accept `json`, so call `api_client.request("DELETE", ..., json=payload)` to keep tests explicit and consistent across verbs.
- **Example:** `api_client.request("DELETE", f"/repositories/{kb}/auto-documentation", json={"promptIds": [...]})`
- **References:**
  - Starlette TestClient documentation ([www.starlette.io](https://www.starlette.io/testclient/)).
  - FastAPI testing docs ([fastapi.tiangolo.com](https://fastapi.tiangolo.com/advanced/testing/)).
