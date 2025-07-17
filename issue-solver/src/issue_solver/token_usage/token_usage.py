"""Token usage value object for tracking LLM usage across issue resolution tasks."""

from dataclasses import dataclass
from datetime import datetime

from issue_solver.models.supported_models import VersionedAIModel


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """
    Represents token usage for a specific operation during issue resolution.
    
    Stores raw usage data from providers to enable future analytics and cost optimization.
    Each operation (message, tool call, agent step) gets its own usage record.
    """
    
    process_id: str
    """The process ID for the issue resolution task"""
    
    operation_id: str
    """Unique identifier for this specific operation (e.g., message sequence, turn number)"""
    
    provider: str
    """The AI provider (e.g., 'anthropic', 'openai')"""
    
    model: VersionedAIModel
    """The AI model used for this operation"""
    
    raw_usage_data: dict
    """The complete usage object from the provider/SDK - kept raw for future-proofing"""
    
    occurred_at: datetime
    """When this operation occurred"""
    
    total_cost_usd: float | None = None
    """Total cost in USD for this operation, if available"""