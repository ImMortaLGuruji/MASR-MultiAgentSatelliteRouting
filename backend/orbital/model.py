import math

from backend.models import Vector3

EARTH_RADIUS_KM = 6371.0


def compute_position(
    orbit_index: int,
    slot_index: int,
    total_slots: int,
    altitude_km: float,
    tick: int,
    total_orbits: int,
) -> Vector3:
    radius = EARTH_RADIUS_KM + altitude_km
    angular_velocity = (2.0 * math.pi) / max(total_slots * 30, 1)
    phase_offset = (2.0 * math.pi * slot_index) / max(total_slots, 1)
    inclination = ((orbit_index + 1) * math.pi) / 12.0
    raan = (2.0 * math.pi * orbit_index) / max(total_orbits, 1)

    theta = (angular_velocity * tick) + phase_offset
    cos_raan = math.cos(raan)
    sin_raan = math.sin(raan)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)
    cos_inc = math.cos(inclination)
    sin_inc = math.sin(inclination)

    x = radius * (cos_raan * cos_theta - sin_raan * sin_theta * cos_inc)
    y = radius * (sin_raan * cos_theta + cos_raan * sin_theta * cos_inc)
    z = radius * (sin_theta * sin_inc)
    return Vector3(x=x, y=y, z=z)


def ground_station_position(lat_deg: float, lon_deg: float) -> Vector3:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    cos_lat = math.cos(lat)
    return Vector3(
        x=EARTH_RADIUS_KM * cos_lat * math.cos(lon),
        y=EARTH_RADIUS_KM * cos_lat * math.sin(lon),
        z=EARTH_RADIUS_KM * math.sin(lat),
    )


def ground_station_visible(station: Vector3, satellite: Vector3) -> bool:
    # Satellite must be above local horizon: dot(station, satellite) > R^2
    return (
        (station.x * satellite.x)
        + (station.y * satellite.y)
        + (station.z * satellite.z)
    ) > (EARTH_RADIUS_KM**2)


def distance(a: Vector3, b: Vector3) -> float:
    return math.sqrt(((a.x - b.x) ** 2) + ((a.y - b.y) ** 2) + ((a.z - b.z) ** 2))


def check_eclipse(position: Vector3) -> bool:
    """True if in the Earth's cylindrical shadow from the +x direction."""
    if position.x < 0:
        dist_from_x_axis_sq = position.y**2 + position.z**2
        if dist_from_x_axis_sq < (EARTH_RADIUS_KM**2):
            return True
    return False
