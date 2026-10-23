# Core Service

Pulumi Python project for provisioning shared services used by the MSDHN platform. The current implementation provisions an Azure Key Vault through a cloud-neutral secret-store interface.

## Current Architecture

The project is run entirely through the Pulumi Automation API. There is no `Pulumi.yaml` or `Pulumi.<stack>.yaml`: `deploy.py` holds the project and stack settings, and runs the program in `program.py` inline.

```text
deploy.py
	-> program.pulumi_program()
			-> stack_context.build_context()
			-> deployments.deploy_key_vault(ctx)
					-> secret_store.create_key_vault(...)
							-> AzureKeyVault (Pulumi ComponentResource)
									-> Azure Native Key Vault
			-> deployments.deploy_front_door(ctx)
					-> front_door.create_front_door(...)
							-> AzureFrontDoor (Pulumi ComponentResource)
```

`program.py` only lists the components to deploy, in order. Settings shared by every component (cloud, provider options, common tags) are built once in `stack_context.py`. Each module in `deployments/` reads its component's config section, calls the capability factory, and exports the outputs. When a component needs another's outputs, pass them as arguments to its `deploy_*` function from `program.py`.

The stack code depends on capability protocols rather than Azure implementation classes. Each capability has a factory for provider selection. Azure is currently the only supported cloud; a future provider can add an implementation that satisfies the relevant capability contract. Capability packages do not read this project's config; that mapping lives in `deployments/`.

```text
deploy.py                # Automation API driver: project + stack config, preview/up
program.py               # The Pulumi program: which components to deploy
stack_context.py         # StackContext: cloud, provider options, common tags
deployments/
	key_vault.py         # keyVault config -> create_key_vault -> exports
	front_door.py        # frontDoor config -> create_front_door -> exports
secret_store/
	base.py              # KeyVault protocol and cloud-neutral arguments
	azure_key_vault.py   # Azure Key Vault implementation
	factory.py           # Provider implementation selection
front_door/
	base.py               # FrontDoor protocol and cloud-neutral arguments
	azure_front_door.py   # Azure Front Door implementation
	factory.py            # Provider implementation selection
```

## Prerequisites

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- Pulumi CLI (the Automation API drives it)
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

All Pulumi config lives in `deploy.py`:

- `PROJECT_CONFIG` applies to every stack. It sets `pulumi:autonaming` to `verbatim`, so each resource's logical name is its physical cloud name. Do not remove it: without it every resource gets a random suffix, and on a deployed stack that replaces every resource.
- `STACK_CONFIG` has one entry per stack. Keys are `pulumi config set --path` paths. Values wrapped in `<...>` are placeholders; `deploy.py` refuses to run while any remain. To add a stack, add an entry.

`resourceGroupName` is shared by all components; every other setting is grouped under one object per component (`keyVault`, `frontDoor`). The Key Vault name must be globally unique and satisfy Azure Key Vault naming requirements.

Provide one subnet resource ID for each subnet allowed to reach the vault, as `keyVault.allowedSubnetIds[0]`, `[1]`, and so on. Key Vault virtual network rules require subnet IDs, not VNet IDs. Each allowed subnet must have the `Microsoft.KeyVault` service endpoint enabled.

`keyVault.roleAssignments` maps each Microsoft Entra object ID to its principal type and one or more full Azure role-definition resource IDs. Use the Entra **object ID** for a group or service principal, not the application's client ID:

```python
'keyVault.roleAssignments["<entra-group-object-id>"].principal_type': "Group",
'keyVault.roleAssignments["<entra-group-object-id>"].role_definition_ids[0]': (
    "/subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/<role-guid>"
),
'keyVault.roleAssignments["<service-principal-object-id>"].principal_type': "ServicePrincipal",
'keyVault.roleAssignments["<service-principal-object-id>"].role_definition_ids[0]': (
    "/subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/<role-guid>"
),
```

Role assignments are created at the Key Vault scope. Select the least-privileged built-in or custom role required by each principal.

`frontDoor.name` is also used as the Front Door endpoint's DNS label and must be globally unique. `frontDoor.originHostName` must be the backend DNS hostname without a scheme, for example `app.example.com`. Optional settings are `frontDoor.originHostHeader`, `frontDoor.healthProbePath` (default `/`) and `frontDoor.routePatterns[0]`, `[1]`, ... (default `/*`).

This creates an Azure Front Door Standard profile, a single HTTPS origin, a health-probed origin group, and a default-domain route that redirects HTTP to HTTPS. It does not configure a custom domain, WAF policy, or private link to the origin.

`azure-native:location` is set per stack in `STACK_CONFIG`. The `cloud` setting is optional and defaults to `azure`. Other values are currently unsupported by the factory.

## Preview and Deploy

```sh
uv run python deploy.py core-service         # preview
uv run python deploy.py core-service --up    # deploy
```

`deploy.py` creates the stack if it does not exist, writes its config, then previews or deploys. Outputs are printed at the end of `--up`. It needs the same environment as the Pulumi CLI: a Pulumi backend login (`pulumi login`, `PULUMI_ACCESS_TOKEN` or `PULUMI_BACKEND_URL`) and `PULUMI_CONFIG_PASSPHRASE`. Always use the same passphrase for a stack; it decrypts the secrets in the stack's state.

Because there is no `Pulumi.yaml` in this directory, `pulumi` CLI commands run here directly do not work; go through `deploy.py`.

## CI/CD (Azure DevOps)

`../azure-pipelines.yml` runs `deploy.py core-service` as a preview on every PR to `main` and on `main` itself, then `deploy.py core-service --up` on `main` once the `core-service-dev` environment's approval check passes. The steps both stages share are in `../deploy-steps.yml`. The one-time Azure DevOps setup (service connection, variable group, environment) is listed at the top of `azure-pipelines.yml`.

The pipeline keeps Pulumi state in Azure Blob storage (`PULUMI_BACKEND_URL=azblob://...`). Run `deploy.py` locally against the same backend, or you will be working on a separate copy of the stack:

```sh
export AZURE_STORAGE_ACCOUNT=<state-storage-account>
pulumi login azblob://<state-container>
```

## Outputs

After deployment, the stack exports:

- `keyVaultId`: Azure resource ID of the Key Vault
- `keyVaultUri`: URI used by clients to access the vault
- `frontDoorProfileId`, `frontDoorEndpointId`, `frontDoorHostName`, `frontDoorUrl`: when Front Door is enabled in `program.py`

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
