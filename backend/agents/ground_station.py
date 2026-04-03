from typing import Callable

from backend.agents.base import BaseAgent
from backend.models import Message


class GroundStationAgent(BaseAgent):
    def __init__(self, station_id: str) -> None:
        super().__init__(station_id)
        self.received_packets: list[str] = []
        self.visible_satellites: list[str] = []

    def handle_message(
        self, message: Message, sender: Callable[[Message], None], tick: int
    ) -> None:
        if message.type == "PACKET_TRANSFER":
            packet_id = str(message.payload["packet_id"])
            self.received_packets.append(packet_id)

    def process_tick(self, tick: int, sender: Callable[[Message], None]) -> None:
        self.process_messages(sender, tick)
