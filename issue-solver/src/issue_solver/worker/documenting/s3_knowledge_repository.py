from botocore.client import BaseClient

from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeRepository,
    KnowledgeBase,
)


def compute_key(base: KnowledgeBase, document_name: str) -> str:
    return f"base/{base.id}/docs/{base.version}/{document_name}"


class S3KnowledgeRepository(KnowledgeRepository):
    def __init__(self, s3_client: BaseClient, bucket_name: str) -> None:
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def contains(self, base: KnowledgeBase, document_name: str) -> bool:
        try:
            head_object = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=compute_key(base, document_name)
            )
            return head_object is not None
        except self.s3_client.exceptions.ClientError:
            return False

    def add(self, base: KnowledgeBase, document_name: str, content: str) -> None:
        self.s3_client.put_object(
            Bucket=self.bucket_name, Key=compute_key(base, document_name), Body=content
        )

    def get_content(self, base: KnowledgeBase, document_name: str) -> str:
        response = self.s3_client.get_object(
            Bucket=self.bucket_name, Key=compute_key(base, document_name)
        )
        return response["Body"].read().decode("utf-8")

    def list_entries(self, base: KnowledgeBase) -> list[str]:
        prefix = f"base/{base.id}/docs/{base.version}/"
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

        document_names = []
        for page in page_iterator:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                document_name = key[len(prefix) :]
                document_names.append(document_name)

        return document_names
