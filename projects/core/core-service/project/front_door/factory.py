from pulumi import ResourceOptions

from .azure_front_door import AzureFrontDoor
from .base import FrontDoor, FrontDoorArgs

_IMPLEMENTATIONS = {"azure": AzureFrontDoor}


def create_front_door(
    cloud: str,
    name: str,
    args: FrontDoorArgs,
    opts: ResourceOptions | None = None,
) -> FrontDoor:
    try:
        implementation = _IMPLEMENTATIONS[cloud]
    except KeyError:
        supported_clouds = ", ".join(sorted(_IMPLEMENTATIONS))
        raise ValueError(
            f"Unsupported cloud {cloud!r}. Supported clouds: {supported_clouds}"
        ) from None

    return implementation(name, args, opts)
