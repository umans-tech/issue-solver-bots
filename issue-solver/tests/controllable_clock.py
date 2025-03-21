from datetime import datetime

from issue_solver.clock import Clock


class ControllableClock(Clock):
    def __init__(self, current_time: datetime):
        self.current_time = current_time

    def set(self, time: datetime) -> None:
        self.current_time = time

    def set_from_iso_format(self, iso_format: str) -> None:
        self.current_time = datetime.fromisoformat(iso_format)

    def now(self) -> datetime:
        return self.current_time
