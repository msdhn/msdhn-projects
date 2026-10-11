import os
from uuid import NAMESPACE_URL, uuid5

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
                public_network_access="Enabled",
                network_acls=azure_native.keyvault.NetworkRuleSetArgs(
                    bypass="AzureServices",
                    default_action="Deny",
                    virtual_network_rules=[
                        azure_native.keyvault.VirtualNetworkRuleArgs(id=subnet_id)
                        for subnet_id in args.allowed_subnet_ids
                    ],
                ),
            ),
            opts=ResourceOptions(parent=self),
        )

        for principal_id, access in args.role_assignments.items():
            for role_definition_id in access.role_definition_ids:
                assignment_id = uuid5(
                    NAMESPACE_URL,
                    f"{name}:{principal_id}:{role_definition_id}",
                )
                azure_native.authorization.RoleAssignment(
                    f"{name}-role-{assignment_id.hex[:12]}",
                    principal_id=principal_id,
                    principal_type=access.principal_type,
                    role_definition_id=role_definition_id,
                    role_assignment_name=str(assignment_id),
                    scope=vault.id,
                    opts=ResourceOptions(parent=self),
                )

        self.vault_id = vault.id
        self.vault_uri = vault.properties.apply(lambda properties: properties.vault_uri)

        self.register_outputs({"vault_id": self.vault_id, "vault_uri": self.vault_uri})
