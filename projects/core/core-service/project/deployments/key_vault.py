import pulumi

from secret_store import (
    KeyVault,
    KeyVaultArgs,
    KeyVaultPrincipalAccess,
    create_key_vault,
)
from stack_context import StackContext


def deploy_key_vault(ctx: StackContext) -> KeyVault:
    config = ctx.config.require_object("keyVault")

    key_vault = create_key_vault(
        cloud=ctx.cloud,
        name=config["name"],
        args=KeyVaultArgs(
            tags=ctx.tags,
            allowed_subnet_ids=config["allowedSubnetIds"],
            role_assignments={
                principal_id: KeyVaultPrincipalAccess(**access)
                for principal_id, access in config["roleAssignments"].items()
            },
        ),
        opts=ctx.opts,
    )

    pulumi.export("keyVaultId", key_vault.vault_id)
    pulumi.export("keyVaultUri", key_vault.vault_uri)

    return key_vault
