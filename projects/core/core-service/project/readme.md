# Core Service

Pulumi Python project for provisioning shared services used by the MSDHN platform. The current implementation provisions an Azure Key Vault through a cloud-neutral secret-store interface.

## Current Architecture

```text
__main__.py
	-> secret_store.create_key_vault(...)
			-> AzureKeyVault (Pulumi ComponentResource)
					-> Azure Native Key Vault
```

The stack code depends on the `KeyVault` protocol rather than the Azure implementation. `secret_store/factory.py` selects the provider implementation. Azure is currently the only supported cloud; a future provider can add an implementation that satisfies the capability contract.

```text
secret_store/
	base.py              # KeyVault protocol and cloud-neutral arguments
	azure_key_vault.py   # Azure Key Vault implementation
	factory.py           # Provider implementation selection
```

## Prerequisites

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- Pulumi CLI
- Azure credentials with permission to create a Key Vault in the target resource group

## Configure

Run commands from this directory:

```sh
uv sync
cp .env.example .env
```

Set the Azure identifiers in `.env`:

```dotenv
ARM_SUBSCRIPTION_ID=<azure-subscription-id>
ARM_TENANT_ID=<microsoft-entra-tenant-id>
```

Set the stack-specific Pulumi values. The Key Vault name must be globally unique and satisfy Azure Key Vault naming requirements.

```sh
pulumi config set resourceGroupName <resource-group-name>
pulumi config set keyVaultName <globally-unique-vault-name>
pulumi config set --path 'allowedSubnetIds[0]' '<subnet-resource-id>'
```

Provide one subnet resource ID for each subnet allowed to reach the vault. Key Vault virtual network rules require subnet IDs, not VNet IDs. Each allowed subnet must have the `Microsoft.KeyVault` service endpoint enabled.

Configure `keyVaultRoleAssignments` as a mapping from each Microsoft Entra object ID to its principal type and one or more full Azure role-definition resource IDs. Use the Entra **object ID** for a group or service principal, not the application's client ID.

```yaml
core-service:keyVaultRoleAssignments:
	<entra-group-object-id>:
		principal_type: Group
		role_definition_ids:
			- /subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/<role-guid>
	<service-principal-object-id>:
		principal_type: ServicePrincipal
		role_definition_ids:
			- /subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/<role-guid>
```

Role assignments are created at the Key Vault scope. Select the least-privileged built-in or custom role required by each principal.

The checked-in `Pulumi.dev.yaml` sets `azure-native:location` to `westeurope`. Change it with Pulumi config if the dev stack should use another supported location:

```sh
pulumi config set azure-native:location <azure-region>
```

The `cloud` Pulumi setting is optional and defaults to `azure`. Other values are currently unsupported by the factory.

## Preview and Deploy

Initialize a stack if one does not already exist, then preview before deploying:

```sh
pulumi stack init dev
pulumi preview
pulumi up
```

Use `pulumi stack select dev` instead of `pulumi stack init dev` when the stack already exists.

## Outputs

After deployment, the stack exports:

- `keyVaultId`: Azure resource ID of the Key Vault
- `keyVaultUri`: URI used by clients to access the vault

Read them with:

```sh
pulumi stack output keyVaultId
pulumi stack output keyVaultUri
```

## Development Checks

Ruff is available as a development dependency:

```sh
uv run ruff check .
uv run ruff format --check .
```

`pre-commit` is a development dependency, and its configuration is at the monorepo root. Install the Git hook from the repository root:

```sh
cd "$(git rev-parse --show-toplevel)"
uv run --project projects/core/core-service/project pre-commit install
```

After installation, run the hooks from this project directory:

```sh
uv run pre-commit run --all-files
```

## Security Notes

The Key Vault is configured to use Azure RBAC authorization. Public network access is enabled so Azure Key Vault firewall rules can allow the configured subnets; the firewall denies traffic by default, while Azure services designated as trusted by Microsoft can bypass the network rules. Requests from other public networks are blocked. This project creates configured Key Vault-scoped role assignments but does not create private endpoints. Do not commit `.env` or place secret values in Pulumi outputs.
