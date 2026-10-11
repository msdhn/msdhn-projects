from pulumi import ResourceOptions

from .azure_key_vault import AzureKeyVault
from .base import KeyVault, KeyVaultArgs

_IMPLEMENTATIONS = {"azure": AzureKeyVault}


def create_key_vault(
    cloud: str,
    name: str,
    args: KeyVaultArgs | None = None,
    opts: ResourceOptions | None = None,
) -> KeyVault:
    try:
        implementation = _IMPLEMENTATIONS[cloud]
    except KeyError:
        supported_clouds = ", ".join(sorted(_IMPLEMENTATIONS))
        raise ValueError(
            f"Unsupported cloud {cloud!r}. Supported clouds: {supported_clouds}"
        ) from None

    return implementation(name, args or KeyVaultArgs(), opts)
