import os

import pulumi
import pulumi_azure_native as azure_native
from dotenv import load_dotenv

from network import HubNetworkArgs, create_hub_network

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

hub_network = create_hub_network(
    cloud,
    "hub-network",
    HubNetworkArgs(tags={"project": "core-hub", "owner": "msdhn"}),
    opts,
)

hub_network.vnet_id.apply(lambda id: pulumi.log.info(f"Hub network ready: {id}"))
