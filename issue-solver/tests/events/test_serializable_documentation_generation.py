from datetime import datetime

from issue_solver.events.domain import DocumentationGenerationRequested
from issue_solver.events.serializable_records import (
    DocumentationGenerationRequestedRecord,
)


def test_serialization_defaults_mode_to_complete_when_absent():
    # Given
    record = DocumentationGenerationRequestedRecord(
        occurred_at=datetime.fromisoformat("2025-01-01T12:00:00+00:00"),
        knowledge_base_id="kb-legacy",
        prompt_id="legacy_doc",
        prompt_description="Legacy",
        code_version="commit-legacy",
        run_id="legacy-run",
        process_id="legacy-process",
    )
    payload = record.model_dump_json()

    # When
    event: DocumentationGenerationRequested = (
        DocumentationGenerationRequestedRecord.model_validate_json(
            payload
        ).to_domain_event()
    )

    # Then
    assert event.mode == "complete"
