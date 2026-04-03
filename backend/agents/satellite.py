from typing import Callable, Dict, List

from backend.agents.base import BaseAgent
from backend.models import Message, PacketState, SatelliteState
from backend.routing import compute_next_hop


class SatelliteAgent(BaseAgent):
    def __init__(
        self,
        state: SatelliteState,
        packet_lookup: Dict[str, PacketState],
        transfer_scheduler: Callable[[str, str, str], None],
        message_factory: Callable[[str, str, str, dict], Message],
        reject_handler: Callable[[str, str, str], bool],
    ) -> None:
        super().__init__(state.satellite_id)
        self.state = state
        self.packet_lookup = packet_lookup
        self.transfer_scheduler = transfer_scheduler
        self.message_factory = message_factory
        self.reject_handler = reject_handler
        self.pending_outgoing: Dict[str, str] = {}

    def set_neighbors(self, neighbors: List[str]) -> None:
        self.state.neighbors = sorted(neighbors)

    def handle_message(
        self, message: Message, sender: Callable[[Message], None], tick: int
    ) -> None:
        if message.type == "LINK_ESTABLISHED":
            neighbor = str(message.payload["neighbor_id"])
            if neighbor not in self.state.neighbors:
                self.state.neighbors.append(neighbor)
                self.state.neighbors.sort()
            return

        if message.type == "LINK_TERMINATED":
            neighbor = str(message.payload["neighbor_id"])
            self.state.neighbors = [
                existing for existing in self.state.neighbors if existing != neighbor
            ]
            return

        if message.type == "PACKET_OFFER":
            packet_id = str(message.payload["packet_id"])
            if (
                len(self.state.packet_queue) < self.state.buffer_capacity
                and packet_id not in self.state.packet_queue
            ):
                accept_message = self.message_factory(
                    self.id, message.sender, "PACKET_ACCEPT", {"packet_id": packet_id}
                )
                sender(accept_message)
            else:
                reject_message = self.message_factory(
                    self.id, message.sender, "PACKET_REJECT", {"packet_id": packet_id}
                )
                sender(reject_message)
            return

        if message.type == "PACKET_ACCEPT":
            packet_id = str(message.payload["packet_id"])
            target = self.pending_outgoing.get(packet_id)
            if target:
                self.transfer_scheduler(packet_id, self.id, target)
                self.pending_outgoing.pop(packet_id, None)
            return

        if message.type == "PACKET_REJECT":
            packet_id = str(message.payload["packet_id"])
            self.pending_outgoing.pop(packet_id, None)
            self.reject_handler(packet_id, self.id, message.sender)

    def process_tick(self, tick: int, sender: Callable[[Message], None]) -> None:
        self.process_messages(sender, tick)
        for packet_id in sorted(self.state.packet_queue):
            packet = self.packet_lookup.get(packet_id)
            if packet is None:
                continue
            next_hop = compute_next_hop(
                self.state.routing_policy, packet, self.id, self.state.neighbors
            )
            if next_hop is None or packet_id in self.pending_outgoing:
                continue
            offer = self.message_factory(
                self.id,
                next_hop,
                "PACKET_OFFER",
                {
                    "packet_id": packet.packet_id,
                    "priority": packet.priority,
                    "size": packet.size,
                    "destination": packet.destination,
                },
            )
            self.pending_outgoing[packet_id] = next_hop
            sender(offer)
