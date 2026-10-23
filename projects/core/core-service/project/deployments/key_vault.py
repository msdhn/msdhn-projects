import pulumi

from secret_store import (
    KeyVault,
    KeyVaultArgs,
    KeyVaultPrincipalAccess,
    create_key_vault,
)


def deploy_key_vault(cloud: str, tags: dict[str, str]) -> KeyVault:
    config = pulumi.Config().require_object("keyVault")

    key_vault = create_key_vault(
        cloud=cloud,
        name=config["name"],
        args=KeyVaultArgs(
            tags=tags,
            allowed_subnet_ids=config.get("allowedSubnetIds", []),
            role_assignments={
                principal_id: KeyVaultPrincipalAccess(**access)
                for principal_id, access in config.get("roleAssignments", {}).items()
            },
        ),
    )

    pulumi.export("keyVaultId", key_vault.vault_id)
    pulumi.export("keyVaultUri", key_vault.vault_uri)

    return key_vault
