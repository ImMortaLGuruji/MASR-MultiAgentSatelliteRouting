from pydantic import BaseModel, Field

from backend.routing import RoutingPolicy


class SpawnPacketRequest(BaseModel):
    source: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    destination: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    priority: int = Field(default=1, ge=0)
    size: int = Field(default=1, ge=1)
    ttl: int | None = Field(default=None, ge=1)


class SetRoutingRequest(BaseModel):
    policy: RoutingPolicy


class ChaosRequest(BaseModel):
    mode: str = "mass_packet_generation"
    count: int = Field(default=10, ge=1, le=1000)
    enabled: bool | None = None


class ConfigUpdateRequest(BaseModel):
    routing_policy: RoutingPolicy | None = None
    drop_on_reject: bool | None = None
    tick_interval: float | None = Field(default=None, gt=0.0)
