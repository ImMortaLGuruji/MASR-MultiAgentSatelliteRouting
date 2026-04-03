from pydantic import BaseModel, Field


class SpawnPacketRequest(BaseModel):
    source: str
    destination: str
    priority: int = Field(default=1, ge=0)
    size: int = Field(default=1, ge=1)
    ttl: int | None = Field(default=None, ge=1)


class SetRoutingRequest(BaseModel):
    policy: str


class ChaosRequest(BaseModel):
    mode: str = "mass_packet_generation"
    count: int = Field(default=10, ge=1)
    enabled: bool | None = None


class ConfigUpdateRequest(BaseModel):
    routing_policy: str | None = None
    drop_on_reject: bool | None = None
    tick_interval: float | None = Field(default=None, gt=0.0)
