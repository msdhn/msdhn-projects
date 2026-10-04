from pulumi import ComponentResource, ResourceOptions

from .base import HubFirewall, HubFirewallArgs

__all__ = ["HubFirewall", "HubFirewallArgs"]


class AzureHubFirewall(ComponentResource):
    def __init__(self, name: str, args: HubFirewallArgs, opts: ResourceOptions = None):
        super().__init__("core-hub:firewall:AzureHubFirewall", name, {}, opts)
