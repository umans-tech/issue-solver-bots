"""create agent message store table

Revision ID: 02e08c46ffff
Revises: 45946eed8e9f
Create Date: 2025-07-18 12:02:53.505342

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "02e08c46ffff"
down_revision: Union[str, None] = "45946eed8e9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE agent_message_store
        (
            message_id   VARCHAR PRIMARY KEY,
            process_id   TEXT                                               NOT NULL,
            agent        TEXT                                               NOT NULL,
            model        TEXT                                               NOT NULL,
            turn         INTEGER                                            NOT NULL,
            message      JSONB                                              NOT NULL,
            message_type TEXT                                               NOT NULL,
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE agent_message_store;")
