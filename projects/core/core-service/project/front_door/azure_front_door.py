import pulumi
import pulumi_azure_native as azure_native
from pulumi import ComponentResource, Output, ResourceOptions

from .base import FrontDoorArgs


class AzureFrontDoor(ComponentResource):
    profile_id: Output[str]
    endpoint_id: Output[str]
    endpoint_host_name: Output[str]
    endpoint_url: Output[str]

    def __init__(
        self,
        name: str,
        args: FrontDoorArgs,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__("core-service:front-door:AzureFrontDoor", name, {}, opts)

        resource_group_name = pulumi.Config().require("resourceGroupName")

        profile = azure_native.cdn.Profile(
            name,
            resource_group_name=resource_group_name,
            profile_name=name,
            location="Global",
            sku=azure_native.cdn.SkuArgs(name="Standard_AzureFrontDoor"),
            tags=args.tags,
            opts=ResourceOptions(parent=self),
        )

        endpoint = azure_native.cdn.AFDEndpoint(
            f"{name}-endpoint",
            profile_name=profile.name,
            resource_group_name=resource_group_name,
            endpoint_name=name,
            location="Global",
            enabled_state="Enabled",
            tags=args.tags,
            opts=ResourceOptions(parent=self),
        )

        origin = azure_native.cdn.AFDOrigin(
            f"{name}-origin",
            profile_name=profile.name,
            resource_group_name=resource_group_name,
            origin_group_name=f"{name}-origin-group",
            origin_name=f"{name}-origin",
            host_name=args.origin_host_name,
            origin_host_header=args.origin_host_header or args.origin_host_name,
            https_port=443,
            http_port=80,
            priority=1,
            weight=1000,
            enabled_state="Enabled",
            enforce_certificate_name_check=True,
            opts=ResourceOptions(parent=self),
        )

        origin_group = azure_native.cdn.OriginGroup(
            f"{name}-origin-group",
            profile_name=profile.name,
            resource_group_name=resource_group_name,
            endpoint_name=endpoint.name,
            origin_group_name=f"{name}-origin-group",
            health_probe_settings=azure_native.cdn.HealthProbeParametersArgs(
                probe_path=args.health_probe_path,
                probe_protocol="Https",
                probe_request_type="GET",
            ),
            origins=[azure_native.cdn.ResourceReferenceArgs(id=origin.id)],
            opts=ResourceOptions(parent=self),
        )

        azure_native.cdn.Route(
            f"{name}-route",
            profile_name=profile.name,
            resource_group_name=resource_group_name,
            endpoint_name=endpoint.name,
            route_name=f"{name}-route",
            origin_group=azure_native.cdn.ResourceReferenceArgs(id=origin_group.id),
            patterns_to_match=args.route_patterns,
            supported_protocols=["Http", "Https"],
            forwarding_protocol="HttpsOnly",
            https_redirect="Enabled",
            link_to_default_domain="Enabled",
            opts=ResourceOptions(parent=self),
        )

        self.profile_id = profile.id
        self.endpoint_id = endpoint.id
        self.endpoint_host_name = endpoint.host_name
        self.endpoint_url = endpoint.host_name.apply(
            lambda host_name: f"https://{host_name}"
        )

        self.register_outputs(
            {
                "profile_id": self.profile_id,
                "endpoint_id": self.endpoint_id,
                "endpoint_host_name": self.endpoint_host_name,
                "endpoint_url": self.endpoint_url,
            }
        )
