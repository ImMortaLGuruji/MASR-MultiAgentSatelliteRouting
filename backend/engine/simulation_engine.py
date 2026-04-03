from __future__ import annotations

from dataclasses import asdict
import random
from typing import Dict, List, Set, Tuple

from backend.agents import GroundStationAgent, SatelliteAgent
from backend.config import Config
from backend.messaging import MessageBus
from backend.metrics import MetricsCollector
from backend.models import LinkState, Message, PacketState, SatelliteState, Transfer
from backend.orbital import compute_position, distance


class SimulationEngine:
    def __init__(self, config: Config) -> None:
        self.tick = 0
        self.config = config
        self.message_bus = MessageBus()
        self.metrics = MetricsCollector()
        self.random = random.Random(config.seed)

        self.agents: Dict[str, GroundStationAgent | SatelliteAgent] = {}
        self.satellites: Dict[str, SatelliteAgent] = {}
        self.ground_stations: Dict[str, GroundStationAgent] = {}
        self.packets: Dict[str, PacketState] = {}

        self.active_links: Dict[Tuple[str, str], LinkState] = {}
        self.previous_link_keys: Set[Tuple[str, str]] = set()
        self.scheduled_transfers: List[Transfer] = []
        self.failed_satellites: Set[str] = set()
        self.network_partition_enabled: bool = False

        self._message_counter = 0
        self._packet_counter = 0

        self._init_agents()

    def _init_agents(self) -> None:
        for orbit_index in range(self.config.num_orbits):
            for slot_index in range(self.config.satellites_per_orbit):
                satellite_id = f"sat-{orbit_index:02d}-{slot_index:02d}"
                state = SatelliteState(
                    satellite_id=satellite_id,
                    orbit_index=orbit_index,
                    position=compute_position(
                        orbit_index=orbit_index,
                        slot_index=slot_index,
                        total_slots=self.config.satellites_per_orbit,
                        altitude_km=self.config.orbital_altitude,
                        tick=self.tick,
                    ),
                    buffer_capacity=self.config.buffer_capacity,
                    bandwidth_capacity=self.config.bandwidth,
                    routing_policy=self.config.routing_policy,
                )
                agent = SatelliteAgent(
                    state,
                    self.packets,
                    self.schedule_transfer,
                    self.create_message,
                    self.handle_packet_reject,
                )
                self.satellites[satellite_id] = agent
                self.agents[satellite_id] = agent

        station = GroundStationAgent("gs-0")
        self.ground_stations[station.id] = station
        self.agents[station.id] = station

    def next_message_id(self) -> str:
        self._message_counter += 1
        return f"msg-{self.tick:08d}-{self._message_counter:08d}"

    def create_message(
        self, sender: str, receiver: str, msg_type: str, payload: dict
    ) -> Message:
        return Message(
            message_id=self.next_message_id(),
            tick=self.tick,
            sender=sender,
            receiver=receiver,
            type=msg_type,
            payload=payload,
        )

    def next_packet_id(self) -> str:
        self._packet_counter += 1
        return f"pkt-{self._packet_counter:08d}"

    def spawn_packet(
        self,
        source: str,
        destination: str,
        priority: int = 1,
        size: int = 1,
        ttl: int | None = None,
    ) -> PacketState:
        if source in self.failed_satellites:
            raise ValueError(f"source satellite '{source}' is currently failed")

        packet_id = self.next_packet_id()
        packet = PacketState(
            packet_id=packet_id,
            source=source,
            destination=destination,
            priority=priority,
            size=size,
            ttl=self.config.packet_ttl if ttl is None else ttl,
            creation_tick=self.tick,
            current_holder=source,
            route_history=[source],
            state="CREATED",
        )
        self.packets[packet_id] = packet
        self.metrics.record_created()

        source_agent = self.satellites.get(source)
        if source_agent is not None:
            source_agent.state.packet_queue.append(packet_id)
            source_agent.state.packet_queue = sorted(
                set(source_agent.state.packet_queue)
            )
            packet.state = "IN_QUEUE"
        return packet

    def reset(self) -> None:
        self.tick = 0
        self.message_bus = MessageBus()
        self.metrics.reset()
        self.random = random.Random(self.config.seed)
        self.packets.clear()
        self.active_links.clear()
        self.previous_link_keys.clear()
        self.scheduled_transfers.clear()
        self.failed_satellites.clear()
        self.network_partition_enabled = False
        self._message_counter = 0
        self._packet_counter = 0
        self.agents.clear()
        self.satellites.clear()
        self.ground_stations.clear()
        self._init_agents()

    def run_tick(self) -> None:
        self.update_orbital_positions()
        self.compute_link_visibility()
        self.generate_link_events()
        self.message_bus.deliver_messages(self._deliver)
        self.process_agents()
        self.process_transfers()
        self.expire_packets()
        self.update_runtime_metrics()
        self.tick += 1

    def set_network_partition(self, enabled: bool) -> None:
        self.network_partition_enabled = enabled

    def disable_random_satellites(self, count: int) -> List[str]:
        available = sorted(
            satellite_id
            for satellite_id in self.satellites.keys()
            if satellite_id not in self.failed_satellites
        )
        if not available:
            return []
        n = min(max(count, 0), len(available))
        chosen = sorted(self.random.sample(available, n))
        self.failed_satellites.update(chosen)
        for satellite_id in chosen:
            sat = self.satellites[satellite_id]
            for packet_id in list(sat.state.packet_queue):
                packet = self.packets.get(packet_id)
                if packet is not None and packet.state not in {
                    "DELIVERED",
                    "DROPPED",
                    "EXPIRED",
                }:
                    packet.state = "DROPPED"
                    self.metrics.record_drop()
            sat.state.packet_queue.clear()
            sat.state.neighbors = []
        return chosen

    def restore_satellites(self, count: int) -> List[str]:
        failed = sorted(self.failed_satellites)
        if not failed:
            return []
        n = min(max(count, 0), len(failed))
        restored = failed[:n]
        for satellite_id in restored:
            self.failed_satellites.remove(satellite_id)
        return restored

    def fluctuate_bandwidth(self) -> None:
        for key in sorted(self.active_links.keys()):
            link = self.active_links[key]
            multiplier = self.random.uniform(0.5, 1.5)
            link.bandwidth = max(1.0, link.bandwidth * multiplier)

    def _deliver(self, message: Message) -> None:
        receiver = self.agents.get(message.receiver)
        if receiver is not None:
            receiver.receive(message)

    def update_orbital_positions(self) -> None:
        for satellite_id in sorted(self.satellites.keys()):
            satellite = self.satellites[satellite_id]
            _, orbit_s, slot_s = satellite_id.split("-")
            orbit_index = int(orbit_s)
            slot_index = int(slot_s)
            satellite.state.position = compute_position(
                orbit_index=orbit_index,
                slot_index=slot_index,
                total_slots=self.config.satellites_per_orbit,
                altitude_km=self.config.orbital_altitude,
                tick=self.tick,
            )

    def compute_link_visibility(self) -> None:
        new_links: Dict[Tuple[str, str], LinkState] = {}
        ids = sorted(self.satellites.keys())
        partition_left: Set[str] = set()
        if self.network_partition_enabled:
            midpoint = len(ids) // 2
            partition_left = set(ids[:midpoint])

        for i, source_id in enumerate(ids):
            if source_id in self.failed_satellites:
                continue
            source = self.satellites[source_id]
            for target_id in ids[i + 1 :]:
                if target_id in self.failed_satellites:
                    continue
                if self.network_partition_enabled:
                    source_left = source_id in partition_left
                    target_left = target_id in partition_left
                    if source_left != target_left:
                        continue
                target = self.satellites[target_id]
                d = distance(source.state.position, target.state.position)
                if d <= self.config.max_link_distance:
                    key = (source_id, target_id)
                    new_links[key] = LinkState(
                        source=source_id,
                        target=target_id,
                        bandwidth=self.config.bandwidth,
                        delay=self.config.propagation_delay,
                        quality=max(0.0, 1.0 - (d / self.config.max_link_distance)),
                        active=True,
                    )
        self.active_links = new_links

        neighbors: Dict[str, List[str]] = {satellite_id: [] for satellite_id in ids}
        for source_id, target_id in sorted(self.active_links.keys()):
            neighbors[source_id].append(target_id)
            neighbors[target_id].append(source_id)
        for satellite_id in ids:
            if satellite_id in self.failed_satellites:
                self.satellites[satellite_id].set_neighbors([])
            else:
                self.satellites[satellite_id].set_neighbors(neighbors[satellite_id])

    def generate_link_events(self) -> None:
        current_link_keys = set(self.active_links.keys())
        established = sorted(current_link_keys - self.previous_link_keys)
        terminated = sorted(self.previous_link_keys - current_link_keys)

        for source_id, target_id in established:
            self.message_bus.send(
                self.create_message(
                    source_id, source_id, "LINK_ESTABLISHED", {"neighbor_id": target_id}
                )
            )
            self.message_bus.send(
                self.create_message(
                    target_id, target_id, "LINK_ESTABLISHED", {"neighbor_id": source_id}
                )
            )

        for source_id, target_id in terminated:
            self.message_bus.send(
                self.create_message(
                    source_id, source_id, "LINK_TERMINATED", {"neighbor_id": target_id}
                )
            )
            self.message_bus.send(
                self.create_message(
                    target_id, target_id, "LINK_TERMINATED", {"neighbor_id": source_id}
                )
            )

        self.previous_link_keys = current_link_keys

    def process_agents(self) -> None:
        for agent_id in sorted(self.agents.keys()):
            if agent_id in self.failed_satellites:
                continue
            agent = self.agents[agent_id]
            agent.process_tick(self.tick, self.message_bus.send)

    def schedule_transfer(self, packet_id: str, source: str, target: str) -> None:
        self.scheduled_transfers.append(
            Transfer(packet_id=packet_id, source=source, target=target)
        )

    def handle_packet_reject(
        self, packet_id: str, source: str, rejected_by: str
    ) -> bool:
        if not self.config.drop_on_reject:
            return False
        packet = self.packets.get(packet_id)
        source_agent = self.satellites.get(source)
        if packet is None or source_agent is None:
            return False
        if packet.current_holder != source:
            return False
        if packet_id not in source_agent.state.packet_queue:
            return False

        source_agent.state.packet_queue = [
            existing
            for existing in source_agent.state.packet_queue
            if existing != packet_id
        ]
        packet.state = "DROPPED"
        self.metrics.record_drop()
        return True

    def process_transfers(self) -> None:
        for transfer in sorted(
            self.scheduled_transfers, key=lambda t: (t.packet_id, t.source, t.target)
        ):
            packet = self.packets.get(transfer.packet_id)
            source_agent = self.satellites.get(transfer.source)

            if packet is None or source_agent is None:
                continue
            if transfer.source in self.failed_satellites:
                continue
            if packet.current_holder != transfer.source:
                continue
            if transfer.packet_id not in source_agent.state.packet_queue:
                continue

            target_sat = self.satellites.get(transfer.target)
            if target_sat is not None:
                if transfer.target in self.failed_satellites:
                    packet.state = "DROPPED"
                    self.metrics.record_drop()
                    source_agent.state.packet_queue = [
                        existing
                        for existing in source_agent.state.packet_queue
                        if existing != transfer.packet_id
                    ]
                    continue
                if (
                    len(target_sat.state.packet_queue)
                    >= target_sat.state.buffer_capacity
                ):
                    packet.state = "DROPPED"
                    self.metrics.record_drop()
                    source_agent.state.packet_queue = [
                        existing
                        for existing in source_agent.state.packet_queue
                        if existing != transfer.packet_id
                    ]
                    continue
                source_agent.state.packet_queue = [
                    existing
                    for existing in source_agent.state.packet_queue
                    if existing != transfer.packet_id
                ]
                target_sat.state.packet_queue.append(transfer.packet_id)
                target_sat.state.packet_queue = sorted(
                    set(target_sat.state.packet_queue)
                )
                packet.current_holder = transfer.target
                packet.route_history.append(transfer.target)
                packet.state = "IN_QUEUE"
                if transfer.target == packet.destination:
                    packet.state = "DELIVERED"
                    target_sat.state.packet_queue = [
                        existing
                        for existing in target_sat.state.packet_queue
                        if existing != transfer.packet_id
                    ]
                    self.metrics.record_delivery(packet, self.tick)
                continue

            target_station = self.ground_stations.get(transfer.target)
            if target_station is not None:
                source_agent.state.packet_queue = [
                    existing
                    for existing in source_agent.state.packet_queue
                    if existing != transfer.packet_id
                ]
                packet.current_holder = transfer.target
                packet.route_history.append(transfer.target)
                packet.state = "DELIVERED"
                self.metrics.record_delivery(packet, self.tick)
                target_station.received_packets.append(packet.packet_id)

        self.scheduled_transfers.clear()

    def expire_packets(self) -> None:
        for packet_id in sorted(self.packets.keys()):
            packet = self.packets[packet_id]
            if packet.state in {"DELIVERED", "DROPPED", "EXPIRED"}:
                continue
            if (self.tick - packet.creation_tick) > packet.ttl:
                packet.state = "EXPIRED"
                holder_sat = self.satellites.get(packet.current_holder)
                if holder_sat is not None:
                    holder_sat.state.packet_queue = [
                        existing
                        for existing in holder_sat.state.packet_queue
                        if existing != packet_id
                    ]
                self.metrics.record_drop()

    def update_runtime_metrics(self) -> None:
        active_satellites = [
            satellite_id
            for satellite_id in sorted(self.satellites.keys())
            if satellite_id not in self.failed_satellites
        ]
        active_links = len(self.active_links)
        n = len(active_satellites)
        possible_links = (n * (n - 1)) // 2
        self.metrics.record_link_utilization(active_links, possible_links)

        queued_packets = 0
        total_capacity = 0
        for satellite_id in active_satellites:
            state = self.satellites[satellite_id].state
            queued_packets += len(state.packet_queue)
            total_capacity += state.buffer_capacity
        self.metrics.record_buffer_usage(queued_packets, total_capacity)

    def snapshot(self) -> dict:
        satellites = {}
        for satellite_id in sorted(self.satellites.keys()):
            state = self.satellites[satellite_id].state
            satellites[satellite_id] = {
                "satellite_id": state.satellite_id,
                "orbit_index": state.orbit_index,
                "position": asdict(state.position),
                "neighbors": sorted(state.neighbors),
                "buffer_capacity": state.buffer_capacity,
                "bandwidth_capacity": state.bandwidth_capacity,
                "packet_queue": sorted(state.packet_queue),
                "routing_policy": state.routing_policy,
            }

        links = []
        for key in sorted(self.active_links.keys()):
            links.append(asdict(self.active_links[key]))

        packets = {}
        for packet_id in sorted(self.packets.keys()):
            packets[packet_id] = asdict(self.packets[packet_id])

        return {
            "tick": self.tick,
            "satellites": satellites,
            "links": links,
            "packets": packets,
            "metrics": self.metrics.snapshot(current_tick=self.tick),
            "failed_satellites": sorted(self.failed_satellites),
            "network_partition_enabled": self.network_partition_enabled,
        }
