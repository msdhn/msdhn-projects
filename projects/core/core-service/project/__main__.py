import os

import pulumi
import pulumi_azure_native as azure_native
from dotenv import load_dotenv
from secret_store import KeyVaultArgs, create_key_vault

load_dotenv()

cloud = pulumi.Config().get("cloud") or "azure"

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
    name=pulumi.Config().require("keyVaultName"),
    args=KeyVaultArgs(tags={"environment": pulumi.get_stack()}),
    opts=opts,
)

pulumi.export("keyVaultId", key_vault.vault_id)
pulumi.export("keyVaultUri", key_vault.vault_uri)
