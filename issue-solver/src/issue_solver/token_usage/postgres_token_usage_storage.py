"""PostgreSQL implementation of token usage storage."""

import json
from datetime import datetime

from issue_solver.models.supported_models import QualifiedAIModel, SupportedAIModel
from .storage import TokenUsageStorage
from .token_usage import TokenUsage


class PostgresTokenUsageStorage(TokenUsageStorage):
    """PostgreSQL implementation of token usage storage."""
    
    def __init__(self, connection):
        """Initialize with a database connection."""
        self.connection = connection
    
    async def store(self, usage: TokenUsage) -> None:
        """Store a single token usage record."""
        await self.connection.execute(
            """
            INSERT INTO process_token_usage (
                process_id,
                operation_id,
                provider,
                model,
                raw_usage_data,
                total_cost_usd,
                occurred_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            usage.process_id,
            usage.operation_id,
            usage.provider,
            str(usage.model),  # Convert VersionedAIModel to string representation
            json.dumps(usage.raw_usage_data),
            usage.total_cost_usd,
            usage.occurred_at,
        )
    
    async def find_by_process_id(self, process_id: str) -> list[TokenUsage]:
        """Retrieve all token usage records for a specific process."""
        rows = await self.connection.fetch(
            """
            SELECT process_id, operation_id, provider, model, 
                   raw_usage_data, total_cost_usd, occurred_at
            FROM process_token_usage
            WHERE process_id = $1
            ORDER BY occurred_at ASC
            """,
            process_id,
        )
        
        usage_records: list[TokenUsage] = []
        for row in rows:
            # Parse the model string back to VersionedAIModel
            model_str = row["model"]
            # Extract model and version from string representation
            if "-" in model_str:
                model_name, version = model_str.rsplit("-", 1)
                # Find the appropriate model enum
                for model_enum in [SupportedAIModel]:
                    try:
                        ai_model = SupportedAIModel(model_name)
                        model = QualifiedAIModel(ai_model=ai_model, version=version)
                        break
                    except ValueError:
                        continue
                else:
                    # Fallback if we can't parse it properly
                    model = QualifiedAIModel(ai_model=SupportedAIModel(model_name))
            else:
                ai_model = SupportedAIModel(model_str)
                model = QualifiedAIModel(ai_model=ai_model)
            
            usage_record = TokenUsage(
                process_id=row["process_id"],
                operation_id=row["operation_id"],
                provider=row["provider"],
                model=model,
                raw_usage_data=json.loads(row["raw_usage_data"]),
                total_cost_usd=row["total_cost_usd"],
                occurred_at=row["occurred_at"],
            )
            usage_records.append(usage_record)
        
        return usage_records