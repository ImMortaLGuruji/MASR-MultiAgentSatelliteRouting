from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    satellites_per_orbit: int = 4
    num_orbits: int = 2
    orbital_altitude: float = 550.0
    max_link_distance: float = 8000.0
    buffer_capacity: int = 64
    bandwidth: float = 100.0
    propagation_delay: float = 0.02
    tick_interval: float = 1.0
    packet_spawn_rate: float = 0.1
    seed: int = 42
    routing_policy: str = "SHORTEST_PATH"
    packet_ttl: int = 100
    drop_on_reject: bool = False
    
    # Energy config
    battery_capacity: float = 100.0
    battery_discharge_rate: float = 2.0
    battery_charge_rate: float = 2.5

    @property
    def total_satellites(self) -> int:
        return self.satellites_per_orbit * self.num_orbits
