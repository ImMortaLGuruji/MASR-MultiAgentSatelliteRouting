from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class ScheduledEvent:
    time: float
    order: int
    event: Any = field(compare=False)


class EventScheduler:
    def __init__(self) -> None:
        self.queue: list[ScheduledEvent] = []
        self._counter = 0

    def schedule(self, time: float, event: Any) -> None:
        self._counter += 1
        heapq.heappush(self.queue, ScheduledEvent(time=time, order=self._counter, event=event))

    def pop_next(self) -> tuple[float, Any]:
        scheduled = heapq.heappop(self.queue)
        return scheduled.time, scheduled.event

    def has_events(self) -> bool:
        return bool(self.queue)
