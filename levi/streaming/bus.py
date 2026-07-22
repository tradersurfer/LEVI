"""In-process, user-scoped pub/sub for agent progress events."""

from __future__ import annotations

import asyncio

from .events import AgentProgressEvent


class EventBus:
    """Deliver events only to clients currently subscribed for their owner."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[AgentProgressEvent]]] = {}

    def subscribe(self, user_id: str) -> asyncio.Queue[AgentProgressEvent]:
        owner = self._validate_user_id(user_id)
        queue: asyncio.Queue[AgentProgressEvent] = asyncio.Queue()
        self._subscribers.setdefault(owner, set()).add(queue)
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue[AgentProgressEvent]) -> None:
        subscribers = self._subscribers.get(user_id)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(user_id, None)

    async def publish(self, event: AgentProgressEvent) -> int:
        subscribers = tuple(self._subscribers.get(event.user_id, ()))
        for queue in subscribers:
            queue.put_nowait(event)
        return len(subscribers)

    def subscriber_count(self, user_id: str) -> int:
        return len(self._subscribers.get(user_id, ()))

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        value = user_id.strip()
        if not value:
            raise ValueError("user_id is required")
        return value
