from __future__ import annotations

from dataclasses import asdict
import math
import random
from typing import Dict, List, Set, Tuple

from backend.agents import GroundStationAgent, SatelliteAgent
from backend.config import Config
from backend.engine.scheduler import EventScheduler
from backend.messaging import MessageBus
from backend.metrics import MetricsCollector
from backend.models import LinkState, Message, PacketState, SatelliteState, Transfer
from backend.orbital import check_eclipse, compute_position, distance


class SimulationEngine:
    def __init__(self, config: Config) -> None:
        self.tick = 0
        self.config = config
        self.message_bus = MessageBus()
        self.scheduler = EventScheduler()
        self.metrics = MetricsCollector()
        self.random = random.Random(config.seed)

        self.agents: Dict[str, GroundStationAgent | SatelliteAgent] = {}
        self.satellites: Dict[str, SatelliteAgent] = {}
        self.ground_stations: Dict[str, GroundStationAgent] = {}
        self.packets: Dict[str, PacketState] = {}

        self.active_links: Dict[Tuple[str, str], LinkState] = {}
        self.link_cache: Dict[Tuple[str, str], List[Tuple[int, int]]] = {}
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
                    self.get_routing_context,
                )
                self.satellites[satellite_id] = agent
                self.agents[satellite_id] = agent

            station = GroundStationAgent("gs-0")
            self.ground_stations[station.id] = station
            self.agents[station.id] = station

    def get_routing_context(self, current_id: str) -> dict:
        adjacency: Dict[str, Set[str]] = {}
        for satellite_id in sorted(self.satellites.keys()):
            adjacency[satellite_id] = set()
        for source_id, target_id in sorted(self.active_links.keys()):
            adjacency[source_id].add(target_id)
            adjacency[target_id].add(source_id)

        predicted_adjacency = {node: set(links) for node, links in adjacency.items()}

        return {
            "tick": self.tick,
            "adjacency": adjacency,
            "predicted_adjacency": predicted_adjacency,
            "failed_satellites": set(self.failed_satellites),
            "network_partition_enabled": self.network_partition_enabled,
            "current_id": current_id,
        }

    def _drop_packet_from_holder(self, packet_id: str, holder_id: str) -> None:
        holder_sat = self.satellites.get(holder_id)
        if holder_sat is not None:
            holder_sat.state.packet_queue = [
                existing
                for existing in holder_sat.state.packet_queue
                if existing != packet_id
            ]
        packet = self.packets.get(packet_id)
        if packet is not None and packet.state not in {
            "DELIVERED",
            "DROPPED",
            "EXPIRED",
        }:
            packet.state = "DROPPED"
            self.metrics.record_drop()

    def _lowest_priority_packet_id(self, packet_ids: List[str]) -> str | None:
        if not packet_ids:
            return None

        def rank(packet_id: str) -> tuple[int, str]:
            packet = self.packets.get(packet_id)
            if packet is None:
                return (-1, packet_id)
            return (packet.priority, packet_id)

        return sorted(packet_ids, key=rank)[0]

    def _enqueue_with_priority_preemption(
        self, satellite_id: str, incoming_packet_id: str
    ) -> bool:
        target_sat = self.satellites.get(satellite_id)
        incoming_packet = self.packets.get(incoming_packet_id)
        if target_sat is None or incoming_packet is None:
            return False

        queue = list(target_sat.state.packet_queue)
        capacity = target_sat.state.buffer_capacity
        if len(queue) < capacity:
            queue.append(incoming_packet_id)
            target_sat.state.packet_queue = sorted(set(queue))
            incoming_packet.state = "IN_QUEUE"
            return True

        evicted_packet_id = self._lowest_priority_packet_id(queue)
        if evicted_packet_id is None:
            return False
        evicted_packet = self.packets.get(evicted_packet_id)
        if evicted_packet is None:
            return False

        if incoming_packet.priority > evicted_packet.priority:
            target_sat.state.packet_queue = [
                existing for existing in queue if existing != evicted_packet_id
            ]
            self._drop_packet_from_holder(evicted_packet_id, satellite_id)

            target_sat.state.packet_queue.append(incoming_packet_id)
            target_sat.state.packet_queue = sorted(set(target_sat.state.packet_queue))
            incoming_packet.state = "IN_QUEUE"
            return True

        return False

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
            admitted = self._enqueue_with_priority_preemption(source, packet_id)
            if not admitted:
                packet.state = "DROPPED"
                self.metrics.record_drop()
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
        self.step()

    def step(self) -> None:
        self.update_orbital_positions()
        self.compute_link_visibility()
        self.generate_link_events()
        self.message_bus.flush()
        self.message_bus.deliver_all(self.agents)
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

            # Energy/Eclipse model update
            satellite.state.in_eclipse = check_eclipse(satellite.state.position)

            if satellite.state.in_eclipse:
                satellite.state.current_battery -= self.config.battery_discharge_rate
            else:
                satellite.state.current_battery += self.config.battery_charge_rate

            satellite.state.current_battery = max(
                0.0, min(self.config.battery_capacity, satellite.state.current_battery)
            )

            # If battery drops to 0, it shuts down. We handle temporary shutdown logically:
            # We enforce failure state if it's dead, but if it recharges we can revive it.
            # However MASR chaos engineering failures are permanent manual triggers typically.
            # Let's cleanly separate it or use `failed_satellites`.
            # If we don't put it in failed_satellites, we can just block it from links
            # in compute_link_visibility. Wait, let's keep it simple:
            # satellite with battery == 0.0 shouldn't form links.

    def compute_link_visibility(self) -> None:
        new_links: Dict[Tuple[str, str], LinkState] = {}
        ids = sorted(self.satellites.keys())
        partition_left: Set[str] = set()
        if self.network_partition_enabled:
            midpoint = len(ids) // 2
            partition_left = set(ids[:midpoint])

        grid: Dict[Tuple[int, int, int], List[str]] = {}
        grid_size = max(self.config.max_link_distance * 0.5, 1.0)
        neighbor_radius = max(1, math.ceil(self.config.max_link_distance / grid_size))
        for sid in ids:
            if sid in self.failed_satellites:
                continue
            sat = self.satellites[sid]
            if sat.state.current_battery <= 0.0:
                continue
            pos = sat.state.position
            gx = int(pos.x // grid_size)
            gy = int(pos.y // grid_size)
            gz = int(pos.z // grid_size)
            grid.setdefault((gx, gy, gz), []).append(sid)

        offsets = [
            (dx, dy, dz)
            for dx in range(-neighbor_radius, neighbor_radius + 1)
            for dy in range(-neighbor_radius, neighbor_radius + 1)
            for dz in range(-neighbor_radius, neighbor_radius + 1)
        ]
        checked_pairs: Set[Tuple[str, str]] = set()
        for cell in sorted(grid.keys()):
            members = sorted(grid[cell])

            for index, sid in enumerate(members):
                source = self.satellites[sid]
                if source.state.current_battery <= 0.0:
                    continue

                for target_id in members[index + 1 :]:
                    pair = tuple(sorted((sid, target_id)))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    target = self.satellites[target_id]
                    if target.state.current_battery <= 0.0:
                        continue
                    if self.network_partition_enabled:
                        if (sid in partition_left) != (target_id in partition_left):
                            continue
                    d = distance(source.state.position, target.state.position)
                    if d <= self.config.max_link_distance:
                        new_links[pair] = LinkState(
                            source=pair[0],
                            target=pair[1],
                            bandwidth=self.config.bandwidth,
                            delay=self.config.propagation_delay,
                            quality=max(0.0, 1.0 - (d / self.config.max_link_distance)),
                            active=True,
                        )

            gx, gy, gz = cell
            for dx, dy, dz in offsets:
                neighbor = (gx + dx, gy + dy, gz + dz)
                if neighbor <= cell:
                    continue
                neighbor_members = grid.get(neighbor)
                if not neighbor_members:
                    continue
                for sid in members:
                    source = self.satellites[sid]
                    if source.state.current_battery <= 0.0:
                        continue
                    for target_id in neighbor_members:
                        pair = tuple(sorted((sid, target_id)))
                        if pair in checked_pairs:
                            continue
                        checked_pairs.add(pair)

                        target = self.satellites[target_id]
                        if target.state.current_battery <= 0.0:
                            continue
                        if self.network_partition_enabled:
                            if (sid in partition_left) != (target_id in partition_left):
                                continue
                        d = distance(source.state.position, target.state.position)
                        if d <= self.config.max_link_distance:
                            new_links[pair] = LinkState(
                                source=pair[0],
                                target=pair[1],
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
        edge = tuple(sorted((source, target)))
        link = self.active_links.get(edge)
        packet = self.packets.get(packet_id)
        if packet is None:
            return
        if link is None:
            bandwidth = self.config.bandwidth
            delay = self.config.propagation_delay
        else:
            bandwidth = link.bandwidth
            delay = link.delay
        transfer_time_ticks = max(
            0,
            math.ceil((packet.size / max(bandwidth, 1.0)) + max(delay, 0.0))
            - 1,
        )
        self.scheduled_transfers.append(
            Transfer(
                packet_id=packet_id,
                source=source,
                target=target,
                ready_tick=self.tick + transfer_time_ticks,
            )
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
        pending: List[Transfer] = []
        for transfer in sorted(
            self.scheduled_transfers,
            key=lambda t: (t.ready_tick, t.packet_id, t.source, t.target),
        ):
            if transfer.ready_tick > self.tick:
                pending.append(transfer)
                continue

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
                    source_agent.state.packet_queue = [
                        existing
                        for existing in source_agent.state.packet_queue
                        if existing != transfer.packet_id
                    ]
                    packet.state = "DROPPED"
                    self.metrics.record_drop()
                    continue
                self.transfer_packet(transfer.packet_id, transfer.source, transfer.target)
                if packet.state in {"DROPPED", "EXPIRED"}:
                    continue

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
                assert packet.current_holder in self.agents
                packet.route_history.append(transfer.target)
                packet.state = "DELIVERED"
                self.metrics.record_delivery(packet, self.tick)
                target_station.received_packets.append(packet.packet_id)

        self.scheduled_transfers = pending

    def transfer_packet(self, packet_id: str, from_id: str, to_id: str) -> None:
        packet = self.packets.get(packet_id)
        source_agent = self.satellites.get(from_id)
        target_agent = self.satellites.get(to_id)
        if packet is None or source_agent is None or target_agent is None:
            return

        assert packet.current_holder == from_id

        source_queue = source_agent.state.packet_queue
        if packet_id in source_queue:
            source_queue.remove(packet_id)

        admitted = self._enqueue_with_priority_preemption(to_id, packet_id)
        if not admitted:
            packet.state = "DROPPED"
            self.metrics.record_drop()
            return

        packet.current_holder = to_id
        packet.route_history.append(to_id)
        assert packet.current_holder in self.agents

        owners = 0
        for satellite_id in sorted(self.satellites.keys()):
            if packet_id in self.satellites[satellite_id].state.packet_queue:
                owners += 1
        assert owners <= 1

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
                "battery_capacity": state.battery_capacity,
                "current_battery": state.current_battery,
                "in_eclipse": state.in_eclipse,
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
