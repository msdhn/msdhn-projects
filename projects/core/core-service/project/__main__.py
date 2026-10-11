import os

import pulumi
import pulumi_azure_native as azure_native
from dotenv import load_dotenv
from secret_store import KeyVaultArgs, KeyVaultPrincipalAccess, create_key_vault

load_dotenv()

cloud = pulumi.Config().get("cloud") or "azure"
config = pulumi.Config()
role_assignments_config = config.require_object("keyVaultRoleAssignments")

opts = None
if cloud == "azure":
    azure_provider = azure_native.Provider(
        "azure",
        subscription_id=os.environ["ARM_SUBSCRIPTION_ID"],
        tenant_id=os.environ["ARM_TENANT_ID"],
        location=pulumi.Config("azure-native").get("location"),
    )
    opts = pulumi.ResourceOptions(providers=[azure_provider])

key_vault = create_key_vault(
    cloud=cloud,
    name=config.require("keyVaultName"),
    args=KeyVaultArgs(
        tags={"environment": pulumi.get_stack()},
        allowed_subnet_ids=config.require_object("allowedSubnetIds"),
        role_assignments={
            principal_id: KeyVaultPrincipalAccess(**access)
            for principal_id, access in role_assignments_config.items()
        },
    ),
    opts=opts,
)

pulumi.export("keyVaultId", key_vault.vault_id)
pulumi.export("keyVaultUri", key_vault.vault_uri)
