from dataclasses import dataclass, field
from typing import Protocol

from pulumi import Output


@dataclass
class KeyVaultArgs:
    tags: dict[str, str] = field(default_factory=dict)


class KeyVault(Protocol):
    """Cloud-neutral outputs callers may rely on."""

    vault_id: Output[str]
    vault_uri: Output[str]
