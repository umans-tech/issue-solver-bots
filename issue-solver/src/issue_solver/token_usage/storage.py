"""Storage interface for token usage tracking."""

from abc import ABC, abstractmethod

from .token_usage import TokenUsage


class TokenUsageStorage(ABC):
    """Abstract interface for storing and retrieving token usage data."""
    
    @abstractmethod
    async def store(self, usage: TokenUsage) -> None:
        """Store a single token usage record."""
        pass
    
    @abstractmethod
    async def find_by_process_id(self, process_id: str) -> list[TokenUsage]:
        """Retrieve all token usage records for a specific process."""
        pass