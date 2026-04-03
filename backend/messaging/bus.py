from typing import Callable, List

from backend.models import Message


class MessageBus:
    def __init__(self) -> None:
        self.queue: List[Message] = []

    def send(self, message: Message) -> None:
        self.queue.append(message)

    def deliver_messages(self, deliver_fn: Callable[[Message], None]) -> None:
        ordered = sorted(
            self.queue,
            key=lambda message: (
                message.tick,
                message.sender,
                message.receiver,
                message.message_id,
            ),
        )
        for message in ordered:
            deliver_fn(message)
        self.queue.clear()
