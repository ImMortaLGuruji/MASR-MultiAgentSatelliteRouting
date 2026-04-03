from abc import ABC, abstractmethod
from typing import Callable, List

from backend.models import Message


class BaseAgent(ABC):
    def __init__(self, agent_id: str) -> None:
        self.id = agent_id
        self.inbox: List[Message] = []

    def receive(self, message: Message) -> None:
        self.inbox.append(message)

    def process_messages(self, sender: Callable[[Message], None], tick: int) -> None:
        ordered = sorted(
            self.inbox,
            key=lambda message: (
                message.tick,
                message.sender,
                message.receiver,
                message.message_id,
            ),
        )
        for message in ordered:
            self.handle_message(message, sender, tick)
        self.inbox.clear()

    @abstractmethod
    def handle_message(
        self, message: Message, sender: Callable[[Message], None], tick: int
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_tick(self, tick: int, sender: Callable[[Message], None]) -> None:
        raise NotImplementedError
