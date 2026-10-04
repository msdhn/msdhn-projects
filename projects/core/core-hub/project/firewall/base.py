from dataclasses import dataclass, field
from typing import Protocol

from pulumi import Output


@dataclass
class HubFirewallArgs:
    tags: dict[str, str] = field(default_factory=dict)


class HubFirewall(Protocol):
    """What callers may rely on, regardless of cloud."""

    endpoint: Output[str]
