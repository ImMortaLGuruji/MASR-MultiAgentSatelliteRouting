from abc import ABC, abstractmethod
from typing import List, Callable, Any
from backend.models import Message

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.id = agent_id
        self.inbox: List[Message] = []

    def receive(self, message: Message) -> None:
        self.inbox.append(message)
        self.inbox.sort(key=lambda m: m.message_id)

    def process_messages(self, sender: Callable[[Message], None], tick: int) -> None:
        for message in self.inbox:
            self.handle_message(message, sender, tick)
        self.inbox.clear()

    @abstractmethod
    def handle_message(self, message: Message, sender: Callable[[Message], None], tick: int) -> None:
        pass

    @abstractmethod
    def process_tick(self, tick: int, sender: Callable[[Message], None]) -> None:
        pass
