import pulumi

from deployments import deploy_key_vault


def pulumi_program() -> None:
    """The core-service Pulumi program. deploy.py runs it inline."""
    cloud = pulumi.Config().get("cloud") or "azure"
    tags = {"environment": pulumi.get_stack()}

    deploy_key_vault(cloud, tags)
    # deploy_front_door(cloud, tags)
