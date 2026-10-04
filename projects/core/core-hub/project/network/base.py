from dataclasses import dataclass, field
from typing import Protocol

from pulumi import Output


@dataclass
class HubNetworkArgs:
    tags: dict[str, str] = field(default_factory=dict)


class HubNetwork(Protocol):
    """What callers may rely on, regardless of cloud."""

    vnet_id: Output[str]
    vnet_name: Output[str]
    subnet_ids: Output[dict[str, str]]  # subnet name -> subnet ID
