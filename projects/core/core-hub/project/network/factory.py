from pulumi import ResourceOptions

from .azure_network import AzureHubNetwork
from .base import HubNetwork, HubNetworkArgs

_IMPLEMENTATIONS = {"azure": AzureHubNetwork}


def create_hub_network(
    cloud: str,
    name: str,
    args: HubNetworkArgs | None = None,
    opts: ResourceOptions | None = None,
) -> HubNetwork:
    try:
        impl = _IMPLEMENTATIONS[cloud]
    except KeyError:
        raise ValueError(
            f"Unsupported cloud '{cloud}'. Expected one of: {sorted(_IMPLEMENTATIONS)}"
        ) from None
    return impl(name, args or HubNetworkArgs(), opts)
