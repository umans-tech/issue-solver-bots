"""add compensating auto-doc prompts event

Revision ID: 7f2fb0a5222d
Revises: 02e08c46ffff
Create Date: 2025-09-24 07:05:07 UTC

"""

import json
from datetime import datetime
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

from issue_solver.agents.docs_prompts import suggested_docs_prompts

# revision identifiers, used by Alembic.
revision: str = "7f2fb0a5222d"
down_revision: Union[str, None] = "02e08c46ffff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


KB_ID = "vs_67ed61bde3d081918932331cff03b071"
USER_ID = "aba06b5f-0ba7-4610-9f24-61d04804027e"
PROCESS_ID = "7ad5a094-5c87-489e-ba96-1f781047e939"
EVENT_ID = "de5d194f-1d9f-4b4d-9a28-3db5ce062f9b"
EVENT_TYPE = "documentation_prompts_defined"
EVENT_OCCURED_AT = datetime.fromisoformat("2025-09-24T09:04:07+02:00")


def upgrade() -> None:
    conn = op.get_bind()
    event_data = {
        "knowledge_base_id": KB_ID,
        "user_id": USER_ID,
        "docs_prompts": {
            "domain_events_glossary.md": suggested_docs_prompts().get(
                "domain_events_glossary.md"
            ),
        },
        "process_id": PROCESS_ID,
        "occurred_at": EVENT_OCCURED_AT.isoformat(),
    }

    conn.execute(
        text(
            """
            INSERT INTO events_store (
                event_id,
                activity_id,
                position,
                event_type,
                data,
                metadata,
                occured_at
            )
            SELECT
                :event_id,
                :activity_id,
                1,
                :event_type,
                (:data)::jsonb,
                '{}'::jsonb,
                :occured_at
            WHERE EXISTS (
                SELECT 1
                FROM events_store
                WHERE data->>'knowledge_base_id' = :kb_id
                LIMIT 1
            )
            """
        ),
        {
            "event_id": EVENT_ID,
            "activity_id": PROCESS_ID,
            "event_type": EVENT_TYPE,
            "data": json.dumps(event_data),
            "occured_at": EVENT_OCCURED_AT,
            "kb_id": KB_ID,
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM events_store WHERE event_id = :event_id"),
        {"event_id": EVENT_ID},
    )
