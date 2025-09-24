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
        base=knowledge_base_key, document_name="doc1.md", content="# Doc 1"
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
        base=knowledge_base_key, document_name="doc1.md", content="# Doc 1"
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
        base=knowledge_base_key, document_name="doc1.md", content="# Doc 1"
    )
    knowledge_repository.add(
        base=knowledge_base_key, document_name="doc2.md", content="# Doc 2"
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
        base=knowledge_base_key, document_name="doc1.md", content="# Doc 1"
    )

    # When
    knowledge_repository.add(
        base=knowledge_base_key, document_name="doc1.md", content="# Doc 1 - Updated"
    )

    # Then
    retrieved_content = knowledge_repository.get_content(
        base=knowledge_base_key, document_name="doc1.md"
    )
    assert retrieved_content == "# Doc 1 - Updated"
