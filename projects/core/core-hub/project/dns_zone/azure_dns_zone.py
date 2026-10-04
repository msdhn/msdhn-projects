from pulumi import ComponentResource, ResourceOptions

from .base import HubPrivateDnsZone, HubPrivateDnsZoneArgs

__all__ = ["HubPrivateDnsZone", "HubPrivateDnsZoneArgs"]


class AzureHubPrivateDnsZone(ComponentResource):
    def __init__(
        self, name: str, args: HubPrivateDnsZoneArgs, opts: ResourceOptions = None
    ):
        super().__init__("core-hub:dns_zone:AzureHubPrivateDnsZone", name, {}, opts)
