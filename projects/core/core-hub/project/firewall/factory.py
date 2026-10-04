from pulumi import ResourceOptions

from .azure_firewall import AzureHubFirewall
from .base import HubFirewall, HubFirewallArgs

_IMPLEMENTATIONS = {"azure": AzureHubFirewall}


def create_hub_firewall(
    cloud: str,
    name: str,
    args: HubFirewallArgs | None = None,
    opts: ResourceOptions | None = None,
) -> HubFirewall:
    try:
        impl = _IMPLEMENTATIONS[cloud]
    except KeyError:
        raise ValueError(
            f"Unsupported cloud '{cloud}'. Expected one of: {sorted(_IMPLEMENTATIONS)}"
        ) from None
    return impl(name, args or HubFirewallArgs(), opts)
