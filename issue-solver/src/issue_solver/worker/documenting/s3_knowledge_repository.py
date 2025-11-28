import json
from pathlib import Path

from botocore.client import BaseClient

from issue_solver.worker.documenting.knowledge_repository import (
    KnowledgeRepository,
    KnowledgeBase,
)


def to_key(base: KnowledgeBase) -> str:
    return f"base/{base.id}/docs/{base.version}/"


def compute_key(base: KnowledgeBase, document_name: str) -> str:
    return Path(to_key(base)).joinpath(document_name).as_posix()


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

    def add(
        self,
        base: KnowledgeBase,
        document_name: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=compute_key(base, document_name),
            Body=content,
        )
        if metadata:
            self._update_manifest(base, document_name, metadata)

    def get_content(self, base: KnowledgeBase, document_name: str) -> str:
        response = self.s3_client.get_object(
            Bucket=self.bucket_name, Key=compute_key(base, document_name)
        )
        return response["Body"].read().decode("utf-8")

    def list_entries(self, base: KnowledgeBase) -> list[str]:
        prefix = to_key(base)
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

        document_names = []
        for page in page_iterator:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                document_name = key[len(str(prefix)) :]
                if document_name in ("__origins__.json", "__metadata__.json"):
                    continue
                document_names.append(document_name)

        return document_names

    def get_metadata(self, base: KnowledgeBase, document_name: str) -> dict[str, str]:
        manifest = self._load_manifest(base)
        return manifest.get(document_name, {})

    @classmethod
    def _manifest_key(cls, base: KnowledgeBase) -> str:
        return Path(to_key(base)).joinpath("__metadata__.json").as_posix()

    def _load_manifest(self, base: KnowledgeBase) -> dict[str, dict[str, str]]:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self._manifest_key(base)
            )
        except self.s3_client.exceptions.ClientError:
            return {}
        body = response["Body"].read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _update_manifest(
        self, base: KnowledgeBase, document_name: str, metadata: dict[str, str]
    ) -> None:
        manifest = self._load_manifest(base)

        existing = manifest.get(document_name, {})
        merged_metadata = {**existing, **metadata}

        manifest[document_name] = merged_metadata
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self._manifest_key(base),
            Body=json.dumps(manifest),
        )
