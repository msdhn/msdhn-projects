import pulumi

from front_door import FrontDoor, FrontDoorArgs, create_front_door


def deploy_front_door(cloud: str, tags: dict[str, str]) -> FrontDoor:
    config = pulumi.Config().require_object("frontDoor")

    front_door = create_front_door(
        cloud=cloud,
        name=config["name"],
        args=FrontDoorArgs(
            origin_host_name=config["originHostName"],
            origin_host_header=config.get("originHostHeader"),
            health_probe_path=config.get("healthProbePath") or "/",
            route_patterns=config.get("routePatterns") or ["/*"],
            tags=tags,
        ),
    )

    pulumi.export("frontDoorProfileId", front_door.profile_id)
    pulumi.export("frontDoorEndpointId", front_door.endpoint_id)
    pulumi.export("frontDoorHostName", front_door.endpoint_host_name)
    pulumi.export("frontDoorUrl", front_door.endpoint_url)

    return front_door
