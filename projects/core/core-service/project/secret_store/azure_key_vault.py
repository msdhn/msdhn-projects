import os

import pulumi
import pulumi_azure_native as azure_native
from pulumi import ComponentResource, Output, ResourceOptions

from .base import KeyVaultArgs


class AzureKeyVault(ComponentResource):
    vault_id: Output[str]
    vault_uri: Output[str]

    def __init__(
        self,
        name: str,
        args: KeyVaultArgs,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__("core-service:secret-store:AzureKeyVault", name, {}, opts)

        config = pulumi.Config()
        azure_config = pulumi.Config("azure-native")

        vault = azure_native.keyvault.Vault(
            name,
            resource_group_name=config.require("resourceGroupName"),
            vault_name=name,
            location=azure_config.require("location"),
            tags=args.tags,
            properties=azure_native.keyvault.VaultPropertiesArgs(
                tenant_id=os.environ["ARM_TENANT_ID"],
                sku=azure_native.keyvault.SkuArgs(family="A", name="standard"),
                enable_rbac_authorization=True,
            ),
            opts=ResourceOptions(parent=self),
        )

        self.vault_id = vault.id
        self.vault_uri = vault.properties.apply(lambda properties: properties.vault_uri)

        self.register_outputs({"vault_id": self.vault_id, "vault_uri": self.vault_uri})
