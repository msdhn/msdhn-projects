from dataclasses import dataclass, field
from typing import Protocol

from pulumi import Output


@dataclass
class FrontDoorArgs:
    origin_host_name: str
    origin_host_header: str | None = None
    health_probe_path: str = "/"
    route_patterns: list[str] = field(default_factory=lambda: ["/*"])
    tags: dict[str, str] = field(default_factory=dict)


class FrontDoor(Protocol):
    """Cloud-neutral outputs callers may rely on."""

    profile_id: Output[str]
    endpoint_id: Output[str]
    endpoint_host_name: Output[str]
    endpoint_url: Output[str]
