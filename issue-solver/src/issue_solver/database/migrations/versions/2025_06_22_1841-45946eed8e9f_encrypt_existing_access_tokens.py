"""encrypt_existing_access_tokens

Revision ID: 45946eed8e9f
Revises: 598646fdaeb0
Create Date: 2025-06-22 18:41:47.067560

"""

import json
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from cryptography.fernet import Fernet


# revision identifiers, used by Alembic.
revision: str = "45946eed8e9f"
down_revision: Union[str, None] = "598646fdaeb0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_encryption_key() -> bytes:
    key_str = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if not key_str:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY environment variable is required for this migration"
        )
    return key_str.encode()


def _encrypt_token(plain_token: str) -> str:
    if not plain_token:
        return plain_token

    fernet = Fernet(_get_encryption_key())
    encrypted_bytes = fernet.encrypt(plain_token.encode())
    return encrypted_bytes.decode()


def _is_encrypted(token: str) -> bool:
    if not token:
        return True

    try:
        fernet = Fernet(_get_encryption_key())
        fernet.decrypt(token.encode())
        return True
    except Exception:
        return False


def upgrade() -> None:
    """Encrypt existing access tokens in repository_connected events."""
    connection = op.get_bind()

    result = connection.execute(
        sa.text("""
        SELECT event_id, data::text as data_json
        FROM events_store 
        WHERE event_type = 'repository_connected'
    """)
    )

    for row in result:
        event_data = json.loads(row.data_json)
        token = event_data.get("access_token", "")

        if token and not _is_encrypted(token):
            encrypted_token = _encrypt_token(token)
            event_data["access_token"] = encrypted_token

            connection.execute(
                sa.text("""
                 UPDATE events_store 
                 SET data = CAST(:data AS jsonb)
                 WHERE event_id = :event_id
             """),
                {"data": json.dumps(event_data), "event_id": row.event_id},
            )


def downgrade() -> None:
    """Downgrade schema."""
    pass
