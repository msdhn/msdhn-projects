"""Create or update a core-service stack with the Pulumi Automation API.

Run from this directory:

    uv run python deploy.py core-service         # preview
    uv run python deploy.py core-service --up    # deploy

This file is the whole Pulumi project definition: the program is
program.pulumi_program, run inline, and all project and stack settings live
below. There is no Pulumi.yaml or Pulumi.<stack>.yaml; the Automation API
writes them into a temporary directory for each run, which is deleted
afterwards.
"""

import argparse
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from pulumi import automation as auto

from program import pulumi_program

PROJECT_DIR = Path(__file__).parent
PROJECT_NAME = "core-service"

# Applied to every stack. Verbatim autonaming makes each resource's logical
# name its physical cloud name; without it every resource gets a random suffix,
# and changing it on a deployed stack replaces every resource.
PROJECT_CONFIG: dict[str, str] = {
    "pulumi:autonaming.mode": "verbatim",
}

# Keys are `pulumi config set --path` paths. Values still wrapped in <...> are
# placeholders and must be filled in before the stack can be used.
STACK_CONFIG: dict[str, dict[str, str]] = {
    "core-service": {
        "azure-native:location": "northeurope",
        "resourceGroupName": "msdhnrg",
        "keyVault.name": "msdhnkv1",
        # Needed once deploy_front_door is enabled in program.py:
        # "frontDoor.name": "<globally-unique-front-door-name>",
        # "frontDoor.originHostName": "<origin-dns-hostname>",
    },
}


def deploy(stack_name: str, up: bool) -> None:
    config = {**PROJECT_CONFIG, **STACK_CONFIG[stack_name]}
    placeholders = [
        key for key, value in config.items() if "<" in key or value.startswith("<")
    ]
    if placeholders:
        raise SystemExit(
            f"Fill in placeholder config for stack {stack_name!r} in deploy.py: "
            + ", ".join(placeholders)
        )

    # Loaded here so the Pulumi CLI and the provider plugins it starts inherit
    # these variables, not only the Pulumi program.
    load_dotenv(PROJECT_DIR / ".env")
    # The default azure-native provider deploys into this subscription and
    # tenant. ARM_* come from .env locally and from the pipeline in CI.
    config["azure-native:subscriptionId"] = os.environ["ARM_SUBSCRIPTION_ID"]
    config["azure-native:tenantId"] = os.environ["ARM_TENANT_ID"]

    with tempfile.TemporaryDirectory(prefix=f"{PROJECT_NAME}-") as work_dir:
        stack = auto.create_or_select_stack(
            stack_name=stack_name,
            project_name=PROJECT_NAME,
            program=pulumi_program,
            opts=auto.LocalWorkspaceOptions(work_dir=work_dir),
        )
        stack.set_all_config(
            {key: auto.ConfigValue(value) for key, value in config.items()},
            path=True,
        )

        if not up:
            stack.preview(on_output=print)
            return

        result = stack.up(on_output=print)
        for name, output in result.outputs.items():
            print(f"{name} = {'[secret]' if output.secret else output.value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stack", choices=sorted(STACK_CONFIG))
    parser.add_argument("--up", action="store_true", help="deploy instead of preview")
    args = parser.parse_args()
    deploy(args.stack, args.up)


if __name__ == "__main__":
    main()
