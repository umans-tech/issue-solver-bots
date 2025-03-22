"""create event store table

Revision ID: 598646fdaeb0
Revises:
Create Date: 2025-03-21 23:54:23.585324

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "598646fdaeb0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE events_store (
                event_id    VARCHAR PRIMARY KEY,
                activity_id          VARCHAR NOT NULL,
                position           BIGINT  NOT NULL,
                event_type         VARCHAR NOT NULL,
                data               JSONB   NOT NULL,
                metadata           JSONB   DEFAULT '{}'::jsonb,
                occured_at         TIMESTAMP WITH TIME ZONE NOT NULL,
                UNIQUE (activity_id, position)
        );
    """)
    op.execute("""
        CREATE INDEX idx_events_store_stream_id ON events_store (activity_id);
    """)
    op.execute("""
        CREATE INDEX idx_events_store_created_at ON events_store (occured_at);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE events_store;")
