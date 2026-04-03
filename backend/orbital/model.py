import math

from backend.models import Vector3


EARTH_RADIUS_KM = 6371.0


def compute_position(
    orbit_index: int, slot_index: int, total_slots: int, altitude_km: float, tick: int
) -> Vector3:
    radius = EARTH_RADIUS_KM + altitude_km
    angular_velocity = (2.0 * math.pi) / max(total_slots * 30, 1)
    phase_offset = (2.0 * math.pi * slot_index) / max(total_slots, 1)
    inclination = ((orbit_index + 1) * math.pi) / 12.0

    theta = (angular_velocity * tick) + phase_offset
    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    z = radius * math.sin(inclination) * math.sin(theta)
    return Vector3(x=x, y=y, z=z)


def distance(a: Vector3, b: Vector3) -> float:
    return math.sqrt(((a.x - b.x) ** 2) + ((a.y - b.y) ** 2) + ((a.z - b.z) ** 2))
