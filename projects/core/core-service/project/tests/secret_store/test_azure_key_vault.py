import pulumi
import pytest

from secret_store import KeyVaultArgs
from secret_store.azure_key_vault import ManagementAzureKeyVault

COMPONENT = "core-service:secret-store:ManagementAzureKeyVault"
VAULT = "azure-native:keyvault:Vault"


@pulumi.runtime.test
def test_registers_component_type(mocks):
    # The type token is part of every child resource's URN: changing it makes
    # Pulumi treat the deployed vault as a new resource and replace it.
    key_vault = ManagementAzureKeyVault("kv-test", KeyVaultArgs())

    def check(_):
        (component,) = mocks.of_type(COMPONENT)
        assert component.name == "kv-test"

    return key_vault.vault_id.apply(check)


@pulumi.runtime.test
def test_vault_uses_name_verbatim_and_stack_config(mocks):
    pulumi.runtime.set_all_config(
        {
            "core-service:resourceGroupName": "rg-core",
            "azure-native:location": "northeurope",
        }
    )
    key_vault = ManagementAzureKeyVault("kv-test", KeyVaultArgs())

    def check(_):
        (vault,) = mocks.of_type(VAULT)
        assert vault.name == "kv-test"
        assert vault.inputs["vaultName"] == "kv-test"
        assert vault.inputs["resourceGroupName"] == "rg-core"
        assert vault.inputs["location"] == "northeurope"

    return key_vault.vault_id.apply(check)


@pulumi.runtime.test
def test_vault_tags_come_from_args(mocks):
    key_vault = ManagementAzureKeyVault(
        "kv-test", KeyVaultArgs(tags={"environment": "test"})
    )

    def check(_):
        (vault,) = mocks.of_type(VAULT)
        assert vault.inputs["tags"] == {"environment": "test"}

    return key_vault.vault_id.apply(check)


@pulumi.runtime.test
def test_vault_properties(mocks, monkeypatch):
    monkeypatch.setenv("ARM_TENANT_ID", "tenant-123")
    key_vault = ManagementAzureKeyVault("kv-test", KeyVaultArgs())

    def check(_):
        (vault,) = mocks.of_type(VAULT)
        properties = vault.inputs["properties"]
        assert properties["tenantId"] == "tenant-123"
        assert properties["sku"] == {"family": "A", "name": "standard"}
        assert properties["enableRbacAuthorization"] is True
        assert properties["publicNetworkAccess"] == "Enabled"

    return key_vault.vault_id.apply(check)


@pulumi.runtime.test
def test_outputs_come_from_the_vault(mocks):
    key_vault = ManagementAzureKeyVault("kv-test", KeyVaultArgs())

    def check(outputs):
        vault_id, vault_uri = outputs
        assert vault_id == "kv-test-id"
        assert vault_uri == "https://kv-test.vault.azure.net/"

    return pulumi.Output.all(key_vault.vault_id, key_vault.vault_uri).apply(check)


@pulumi.runtime.test
def test_missing_resource_group_config_fails(mocks):
    pulumi.runtime.set_all_config({"azure-native:location": "westeurope"})

    with pytest.raises(pulumi.ConfigMissingError, match="resourceGroupName"):
        ManagementAzureKeyVault("kv-test", KeyVaultArgs())


@pulumi.runtime.test
def test_missing_tenant_id_fails(mocks, monkeypatch):
    monkeypatch.delenv("ARM_TENANT_ID")

    with pytest.raises(KeyError, match="ARM_TENANT_ID"):
        ManagementAzureKeyVault("kv-test", KeyVaultArgs())
