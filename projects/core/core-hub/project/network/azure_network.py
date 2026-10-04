from pulumi import ComponentResource, Output, ResourceOptions

from .base import HubNetwork, HubNetworkArgs

__all__ = ["HubNetwork", "HubNetworkArgs"]

_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000000"
_RESOURCE_GROUP = "rg-core-hub"
_VNET_NAME = "vnet-core-hub"
_VNET_ID = (
    f"/subscriptions/{_SUBSCRIPTION_ID}/resourceGroups/{_RESOURCE_GROUP}"
    f"/providers/Microsoft.Network/virtualNetworks/{_VNET_NAME}"
)
_SUBNET_NAMES = ["AzureFirewallSubnet", "GatewaySubnet", "snet-shared-services"]


class AzureHubNetwork(ComponentResource):
    vnet_id: Output[str]
    vnet_name: Output[str]
    subnet_ids: Output[dict[str, str]]

    def __init__(
        self, name: str, args: HubNetworkArgs, opts: ResourceOptions | None = None
    ) -> None:
        super().__init__("core-hub:network:AzureHubNetwork", name, {}, opts)

        # Hardcoded placeholder values until the real Azure resources are defined.
        self.vnet_id = Output.from_input(_VNET_ID)
        self.vnet_name = Output.from_input(_VNET_NAME)
        self.subnet_ids = Output.from_input(
            {subnet: f"{_VNET_ID}/subnets/{subnet}" for subnet in _SUBNET_NAMES}
        )

        self.register_outputs(
            {
                "vnet_id": self.vnet_id,
                "vnet_name": self.vnet_name,
                "subnet_ids": self.subnet_ids,
            }
        )
