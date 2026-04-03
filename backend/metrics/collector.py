from dataclasses import dataclass
from typing import Dict, Union

from backend.models import PacketState


MetricValue = Union[int, float]


@dataclass
class MetricsCollector:
    total_packets: int = 0
    delivered_packets: int = 0
    dropped_packets: int = 0
    total_latency: int = 0
    delivered_bytes: int = 0
    link_utilization_sum: float = 0.0
    link_utilization_samples: int = 0
    buffer_utilization_sum: float = 0.0
    buffer_utilization_samples: int = 0

    def record_created(self) -> None:
        self.total_packets += 1

    def record_delivery(self, packet: PacketState, current_tick: int) -> None:
        self.delivered_packets += 1
        self.total_latency += max(current_tick - packet.creation_tick, 0)
        self.delivered_bytes += packet.size

    def record_drop(self) -> None:
        self.dropped_packets += 1

    def record_link_utilization(self, active_links: int, possible_links: int) -> None:
        utilization = 0.0
        if possible_links > 0:
            utilization = active_links / possible_links
        self.link_utilization_sum += utilization
        self.link_utilization_samples += 1

    def record_buffer_usage(self, queued_packets: int, total_capacity: int) -> None:
        usage = 0.0
        if total_capacity > 0:
            usage = queued_packets / total_capacity
        self.buffer_utilization_sum += usage
        self.buffer_utilization_samples += 1

    def reset(self) -> None:
        self.total_packets = 0
        self.delivered_packets = 0
        self.dropped_packets = 0
        self.total_latency = 0
        self.delivered_bytes = 0
        self.link_utilization_sum = 0.0
        self.link_utilization_samples = 0
        self.buffer_utilization_sum = 0.0
        self.buffer_utilization_samples = 0

    def snapshot(self, current_tick: int = 0) -> Dict[str, MetricValue]:
        avg_latency = 0.0
        if self.delivered_packets > 0:
            avg_latency = self.total_latency / self.delivered_packets
        delivery_ratio = 0.0
        if self.total_packets > 0:
            delivery_ratio = self.delivered_packets / self.total_packets
        throughput = 0.0
        if current_tick > 0:
            throughput = self.delivered_bytes / current_tick
        link_utilization = 0.0
        if self.link_utilization_samples > 0:
            link_utilization = self.link_utilization_sum / self.link_utilization_samples
        satellite_buffer_usage = 0.0
        if self.buffer_utilization_samples > 0:
            satellite_buffer_usage = (
                self.buffer_utilization_sum / self.buffer_utilization_samples
            )
        packet_drop_rate = 0.0
        if self.total_packets > 0:
            packet_drop_rate = self.dropped_packets / self.total_packets
        return {
            "total_packets": self.total_packets,
            "delivered_packets": self.delivered_packets,
            "dropped_packets": self.dropped_packets,
            "average_latency": avg_latency,
            "packet_delivery_ratio": delivery_ratio,
            "throughput": throughput,
            "link_utilization": link_utilization,
            "satellite_buffer_usage": satellite_buffer_usage,
            "packet_drop_rate": packet_drop_rate,
        }
