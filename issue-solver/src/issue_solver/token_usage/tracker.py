"""Token usage tracking service."""

from .storage import TokenUsageStorage
from .token_usage import TokenUsage


class TokenUsageTracker:
    """Service for tracking token usage across issue resolution operations."""
    
    def __init__(self, storage: TokenUsageStorage):
        """Initialize the tracker with a storage backend."""
        self.storage = storage
    
    async def record_usage(self, usage: TokenUsage) -> None:
        """Record token usage for an operation."""
        await self.storage.store(usage)
    
    async def get_usage_for_process(self, process_id: str) -> list[TokenUsage]:
        """Get all token usage records for a specific process."""
        return await self.storage.find_by_process_id(process_id)