from deployments import deploy_key_vault
from stack_context import build_context


def pulumi_program() -> None:
    """The core-service Pulumi program. deploy.py runs it inline."""
    ctx = build_context()

    deploy_key_vault(ctx)
    # deploy_front_door(ctx)
