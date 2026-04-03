from dataclasses import dataclass

from backend.models import PacketState


@dataclass
class MetricsCollector:
    total_packets: int = 0
    delivered_packets: int = 0
    dropped_packets: int = 0
    total_latency: int = 0

    def record_created(self) -> None:
        self.total_packets += 1

    def record_delivery(self, packet: PacketState, current_tick: int) -> None:
        self.delivered_packets += 1
        self.total_latency += max(current_tick - packet.creation_tick, 0)

    def record_drop(self) -> None:
        self.dropped_packets += 1

    def reset(self) -> None:
        self.total_packets = 0
        self.delivered_packets = 0
        self.dropped_packets = 0
        self.total_latency = 0

    def snapshot(self) -> dict:
        avg_latency = 0.0
        if self.delivered_packets > 0:
            avg_latency = self.total_latency / self.delivered_packets
        delivery_ratio = 0.0
        if self.total_packets > 0:
            delivery_ratio = self.delivered_packets / self.total_packets
        return {
            "total_packets": self.total_packets,
            "delivered_packets": self.delivered_packets,
            "dropped_packets": self.dropped_packets,
            "average_latency": avg_latency,
            "packet_delivery_ratio": delivery_ratio,
        }
