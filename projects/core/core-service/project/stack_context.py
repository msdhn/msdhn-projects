import os
from dataclasses import dataclass

import pulumi
import pulumi_azure_native as azure_native


@dataclass(frozen=True)
class StackContext:
    """Settings shared by every component deployed in this stack."""

    cloud: str
    config: pulumi.Config
    opts: pulumi.ResourceOptions | None
    tags: dict[str, str]


def build_context() -> StackContext:
    config = pulumi.Config()
    cloud = config.get("cloud") or "azure"

    opts = None
    if cloud == "azure":
        azure_provider = azure_native.Provider(
            "azure",
            subscription_id=os.environ["ARM_SUBSCRIPTION_ID"],
            tenant_id=os.environ["ARM_TENANT_ID"],
            location=pulumi.Config("azure-native").get("location"),
        )
        opts = pulumi.ResourceOptions(providers=[azure_provider])

    return StackContext(
        cloud=cloud,
        config=config,
        opts=opts,
        tags={"environment": pulumi.get_stack()},
    )
