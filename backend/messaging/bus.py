from typing import Any, Callable, List

from backend.models import Message

class MessageBus:
    def __init__(self) -> None:
        self.current_queue: List[Message | dict[str, Any]] = []
        self.next_queue: List[Message | dict[str, Any]] = []

    def send(self, message: Message | dict[str, Any]) -> None:
        self.next_queue.append(message)

    def flush(self) -> None:
        self.current_queue = self.next_queue
        self.next_queue = []

        def sort_key(message: Message | dict[str, Any]) -> tuple[Any, Any, Any, Any]:
            if isinstance(message, dict):
                return (
                    message["tick"],
                    message["sender"],
                    message["receiver"],
                    message["message_id"],
                )
            return (
                message.tick,
                message.sender,
                message.receiver,
                message.message_id,
            )

        self.current_queue.sort(key=sort_key)

    def deliver_all(self, target: Callable[[Message], None] | dict[str, Any]) -> None:
        for message in self.current_queue:
            if isinstance(target, dict):
                receiver = (
                    message["receiver"]
                    if isinstance(message, dict)
                    else message.receiver
                )
                target[receiver].receive(message)
            else:
                target(message)

        self.current_queue.clear()

    def deliver_messages(self, deliver_fn: Callable[[Message], None]) -> None:
        self.flush()
        self.deliver_all(deliver_fn)
