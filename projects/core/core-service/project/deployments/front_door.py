import pulumi

from front_door import FrontDoor, FrontDoorArgs, create_front_door
from stack_context import StackContext


def deploy_front_door(ctx: StackContext) -> FrontDoor:
    config = ctx.config.require_object("frontDoor")

    front_door = create_front_door(
        cloud=ctx.cloud,
        name=config["name"],
        args=FrontDoorArgs(
            origin_host_name=config["originHostName"],
            origin_host_header=config.get("originHostHeader"),
            health_probe_path=config.get("healthProbePath") or "/",
            route_patterns=config.get("routePatterns") or ["/*"],
            tags=ctx.tags,
        ),
        opts=ctx.opts,
    )

    pulumi.export("frontDoorProfileId", front_door.profile_id)
    pulumi.export("frontDoorEndpointId", front_door.endpoint_id)
    pulumi.export("frontDoorHostName", front_door.endpoint_host_name)
    pulumi.export("frontDoorUrl", front_door.endpoint_url)

    return front_door
