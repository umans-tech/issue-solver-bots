"""create process token usage table

Revision ID: 4a8b5c6d7e9f
Revises: 45946eed8e9f
Create Date: 2025-01-20 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a8b5c6d7e9f"
down_revision: Union[str, None] = "45946eed8e9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE process_token_usage (
            id SERIAL PRIMARY KEY,
            process_id VARCHAR NOT NULL,
            operation_id VARCHAR NOT NULL,
            provider VARCHAR NOT NULL,
            model VARCHAR NOT NULL,
            raw_usage_data JSONB NOT NULL,
            total_cost_usd DECIMAL(10,4),
            occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX idx_process_token_usage_process_id ON process_token_usage(process_id);
    """)
    op.execute("""
        CREATE INDEX idx_process_token_usage_occurred_at ON process_token_usage(occurred_at);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE process_token_usage;")