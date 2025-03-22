from abc import ABC, abstractmethod
from datetime import datetime, UTC


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass


class UTCSystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
