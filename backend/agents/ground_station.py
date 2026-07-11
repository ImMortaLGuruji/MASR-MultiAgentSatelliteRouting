from typing import Callable

from backend.agents.base import BaseAgent
from backend.models import Message, Vector3


class GroundStationAgent(BaseAgent):
    def __init__(
        self,
        station_id: str,
        position: Vector3,
        message_factory: Callable[[str, str, str, dict], Message] | None = None,
    ) -> None:
        super().__init__(station_id)
        self.received_packets: list[str] = []
        self.visible_satellites: list[str] = []
        self.position = position
        self._message_factory = message_factory
        self._counter = 0

    def _make_message(
        self, tick: int, receiver: str, msg_type: str, payload: dict
    ) -> Message:
        if self._message_factory is not None:
            return self._message_factory(self.id, receiver, msg_type, payload)
        # Fallback: generate a local ID if no factory is available
        self._counter += 1
        return Message(
            message_id=f"gs-{self.id}-{tick:08d}-{self._counter:08d}",
            tick=tick,
            sender=self.id,
            receiver=receiver,
            type=msg_type,
            payload=payload,
        )

    def handle_message(
        self, message: Message, sender: Callable[[Message], None], tick: int
    ) -> None:
        # FIX: Ground stations must respond to PACKET_OFFER with PACKET_ACCEPT.
        # Without this, satellite agents set pending_outgoing[packet_id] = "gs-0"
        # and wait for an accept that never comes, so no transfer is ever scheduled
        # and packets destined for the ground station remain stuck forever.
        if message.type == "PACKET_OFFER":
            packet_id = str(message.payload["packet_id"])
            accept = self._make_message(
                tick, message.sender, "PACKET_ACCEPT", {"packet_id": packet_id}
            )
            sender(accept)
            return

        if message.type == "PACKET_TRANSFER":
            packet_id = str(message.payload["packet_id"])
            self.received_packets.append(packet_id)

    def process_tick(self, tick: int, sender: Callable[[Message], None]) -> None:
        self.process_messages(sender, tick)
