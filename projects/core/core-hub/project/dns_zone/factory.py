from pulumi import ResourceOptions

from .azure_dns_zone import AzureHubPrivateDnsZone
from .base import HubPrivateDnsZone, HubPrivateDnsZoneArgs

_IMPLEMENTATIONS = {"azure": AzureHubPrivateDnsZone}


def create_hub_private_dns_zone(
    cloud: str,
    name: str,
    args: HubPrivateDnsZoneArgs | None = None,
    opts: ResourceOptions | None = None,
) -> HubPrivateDnsZone:
    try:
        impl = _IMPLEMENTATIONS[cloud]
    except KeyError:
        raise ValueError(
            f"Unsupported cloud '{cloud}'. Expected one of: {sorted(_IMPLEMENTATIONS)}"
        ) from None
    return impl(name, args or HubPrivateDnsZoneArgs(), opts)
