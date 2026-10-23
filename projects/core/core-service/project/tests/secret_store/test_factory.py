import pulumi
import pytest

from secret_store import KeyVaultArgs, create_key_vault
from secret_store.azure_key_vault import ManagementAzureKeyVault

VAULT = "azure-native:keyvault:Vault"


@pulumi.runtime.test
def test_azure_creates_the_azure_implementation(mocks):
    key_vault = create_key_vault("azure", "kv-test", KeyVaultArgs())

    assert isinstance(key_vault, ManagementAzureKeyVault)


def test_unsupported_cloud_raises_and_lists_supported_clouds():
    with pytest.raises(
        ValueError, match=r"Unsupported cloud 'aws'\. Supported clouds: azure"
    ):
        create_key_vault("aws", "kv-test")


@pulumi.runtime.test
def test_missing_args_default_to_empty_args(mocks):
    key_vault = create_key_vault("azure", "kv-test")

    def check(_):
        (vault,) = mocks.of_type(VAULT)
        assert vault.inputs.get("tags", {}) == {}

    return key_vault.vault_id.apply(check)
