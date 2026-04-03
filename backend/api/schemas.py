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
