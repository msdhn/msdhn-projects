from dataclasses import dataclass, field
from typing import Literal, Protocol

from pulumi import Output


@dataclass
class KeyVaultPrincipalAccess:
    principal_type: Literal["Group", "ServicePrincipal"]
    role_definition_ids: list[str]


@dataclass
class KeyVaultArgs:
    tags: dict[str, str] = field(default_factory=dict)
    allowed_subnet_ids: list[str] = field(default_factory=list)
    role_assignments: dict[str, KeyVaultPrincipalAccess] = field(default_factory=dict)


class KeyVault(Protocol):
    """Cloud-neutral outputs callers may rely on."""

    vault_id: Output[str]
    vault_uri: Output[str]
