"""Pulumi mocks shared by all tests.

Under mocks there is no Pulumi engine and no cloud: every resource a test
creates is handed to RecordingMocks, which records its inputs so the test can
assert on exactly what would be sent to the provider.

Tests that create resources must be decorated with @pulumi.runtime.test, which
waits for every resource to finish registering before the test ends.
"""

import asyncio
from collections.abc import Iterator

import pulumi
import pytest

PROJECT = "core-service"


class RecordingMocks(pulumi.runtime.Mocks):
    def __init__(self) -> None:
        self.resources: list[pulumi.runtime.MockResourceArgs] = []

    def new_resource(self, args: pulumi.runtime.MockResourceArgs) -> tuple[str, dict]:
        self.resources.append(args)
        state = dict(args.inputs)
        if args.typ == "azure-native:keyvault:Vault":
            # An output Azure computes when it creates the vault.
            state["properties"] = {
                **state.get("properties", {}),
                "vaultUri": f"https://{args.name}.vault.azure.net/",
            }
        return f"{args.name}-id", state

    def call(self, args: pulumi.runtime.MockCallArgs) -> dict:
        return {}

    def of_type(self, typ: str) -> list[pulumi.runtime.MockResourceArgs]:
        return [resource for resource in self.resources if resource.typ == typ]


@pytest.fixture
def mocks(monkeypatch: pytest.MonkeyPatch) -> Iterator[RecordingMocks]:
    """A fresh mock engine, with the config and environment components need."""
    # Python 3.14 no longer creates an event loop on demand; Pulumi needs one.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    recording = RecordingMocks()
    pulumi.runtime.set_mocks(recording, project=PROJECT, stack="test", preview=False)
    pulumi.runtime.set_all_config(
        {
            f"{PROJECT}:resourceGroupName": "rg-test",
            "azure-native:location": "westeurope",
        }
    )
    monkeypatch.setenv("ARM_TENANT_ID", "tenant-test")

    yield recording

    asyncio.set_event_loop(None)
    loop.close()
