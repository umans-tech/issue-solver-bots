import pytest

from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeRepository,
    KnowledgeBase,
)


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_add_and_check_document_existence(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb1", "sha1")

    # When
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "auto"},
    )

    # Then
    assert knowledge_repository.contains(
        base=knowledge_base_key, document_name="doc1.md"
    )

    assert (
        knowledge_repository.get_content(
            base=knowledge_base_key, document_name="doc1.md"
        )
        == "# Doc 1"
    )


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_add_each_doc_to_its_knowledge_base(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb1", "sha1")

    # When
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "repo"},
    )

    # Then
    assert not knowledge_repository.contains(
        base=KnowledgeBase("kb2", "sha1"), document_name="doc1.md"
    )


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_not_find_nonexistent_document(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb1", "sha1")

    # When / Then
    assert not knowledge_repository.contains(
        base=knowledge_base_key, document_name="nonexistent_doc.md"
    )


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_list_documents(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb1", "sha1")
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "auto"},
    )
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc2.md",
        content="# Doc 2",
        metadata={"origin": "repo"},
    )

    # When
    documents = knowledge_repository.list_entries(base=knowledge_base_key)

    # Then
    assert set(documents) == {"doc1.md", "doc2.md"}


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_overwrite_document_with_same_name(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb1", "sha1")
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "auto"},
    )

    # When
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1 - Updated",
        metadata={"origin": "repo"},
    )

    # Then
    retrieved_content = knowledge_repository.get_content(
        base=knowledge_base_key, document_name="doc1.md"
    )
    assert retrieved_content == "# Doc 1 - Updated"


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_store_doc_origin(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb-origin", "sha1")

    # When
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "auto"},
    )

    # Then
    assert (
        knowledge_repository.get_origin(
            base=knowledge_base_key, document_name="doc1.md"
        )
        == "auto"
    )


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_update_origin_on_overwrite(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb-origin", "sha1")
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "auto"},
    )

    # When
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1b",
        metadata={"origin": "repo"},
    )

    # Then
    assert (
        knowledge_repository.get_origin(
            base=knowledge_base_key, document_name="doc1.md"
        )
        == "repo"
    )


@pytest.mark.asyncio
async def test_s3_knowledge_repo_should_return_none_when_origin_missing(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb-origin", "sha2")

    # When
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata=None,
    )

    # Then
    assert (
        knowledge_repository.get_origin(
            base=knowledge_base_key, document_name="doc1.md"
        )
        is None
    )


@pytest.mark.asyncio
async def test_s3_manifest_merge_should_preserve_previous_metadata_when_approving(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb-merge", "sha1")
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={"origin": "auto", "process_id": "p-123"},
    )

    # When
    knowledge_repository._update_manifest(  # type: ignore[attr-defined]
        knowledge_base_key,
        "doc1.md",
        {
            "approved_by_id": "user-1",
            "approved_by_name": "Pat Approver",
            "approved_at": "2025-11-28T10:00:00Z",
        },
    )

    # Then
    metadata = knowledge_repository.get_metadata(
        base=knowledge_base_key, document_name="doc1.md"
    )
    assert metadata == {
        "origin": "auto",
        "process_id": "p-123",
        "approved_by_id": "user-1",
        "approved_by_name": "Pat Approver",
        "approved_at": "2025-11-28T10:00:00Z",
    }


@pytest.mark.asyncio
async def test_s3_manifest_merge_should_replace_existing_approval_fields_only(
    knowledge_repository: KnowledgeRepository,
):
    # Given
    knowledge_base_key = KnowledgeBase("kb-merge", "sha2")
    knowledge_repository.add(
        base=knowledge_base_key,
        document_name="doc1.md",
        content="# Doc 1",
        metadata={
            "origin": "auto",
            "process_id": "p-123",
            "approved_by_id": "user-1",
            "approved_by_name": "Pat Approver",
            "approved_at": "2025-11-28T10:00:00Z",
        },
    )

    # When
    knowledge_repository._update_manifest(  # type: ignore[attr-defined]
        knowledge_base_key,
        "doc1.md",
        {
            "approved_by_id": "user-2",
            "approved_by_name": "Riley Reviewer",
            "approved_at": "2025-11-28T11:15:00Z",
        },
    )

    # Then
    metadata = knowledge_repository.get_metadata(
        base=knowledge_base_key, document_name="doc1.md"
    )
    assert metadata == {
        "origin": "auto",
        "process_id": "p-123",
        "approved_by_id": "user-2",
        "approved_by_name": "Riley Reviewer",
        "approved_at": "2025-11-28T11:15:00Z",
    }
