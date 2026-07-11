from dataclasses import dataclass
import os


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    satellites_per_orbit: int = _env_int("MASR_SATELLITES_PER_ORBIT", 6)
    num_orbits: int = _env_int("MASR_NUM_ORBITS", 3)
    orbital_altitude: float = _env_float("MASR_ORBITAL_ALTITUDE_KM", 550.0)
    max_link_distance: float = _env_float("MASR_MAX_LINK_DISTANCE_KM", 12000.0)
    buffer_capacity: int = _env_int("MASR_BUFFER_CAPACITY", 128)
    bandwidth: float = _env_float("MASR_BANDWIDTH", 150.0)
    propagation_delay: float = _env_float("MASR_PROPAGATION_DELAY", 0.01)
    tick_interval: float = _env_float("MASR_TICK_INTERVAL", 0.5)
    packet_spawn_rate: float = _env_float("MASR_PACKET_SPAWN_RATE", 0.2)
    seed: int = _env_int("MASR_SEED", 42)
    routing_policy: str = os.getenv("MASR_ROUTING_POLICY", "SHORTEST_PATH")
    packet_ttl: int = _env_int("MASR_PACKET_TTL", 200)
    packet_retention_ticks: int = _env_int("MASR_PACKET_RETENTION_TICKS", 10)
    drop_on_reject: bool = _env_bool("MASR_DROP_ON_REJECT", False)

    ground_station_lat_deg: float = _env_float("MASR_GS_LAT_DEG", 0.0)
    ground_station_lon_deg: float = _env_float("MASR_GS_LON_DEG", 0.0)
    contact_prediction_horizon_ticks: int = _env_int(
        "MASR_CONTACT_PREDICTION_HORIZON_TICKS", 6
    )

    # Energy config
    battery_capacity: float = 100.0
    battery_discharge_rate: float = 2.0
    battery_charge_rate: float = 2.5

    @property
    def total_satellites(self) -> int:
        return self.satellites_per_orbit * self.num_orbits
