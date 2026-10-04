# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Pulumi (Python) infrastructure-as-code for a data analytics and AI platform.
The repo is at an early scaffolding stage: most directories are empty
placeholders, and only `projects/core/core-hub` has any code so far.

## Architecture: hub and spoke

- **Hub (core stack)**: one subscription, shared by all customers. Provides the
  hub network and core/shared services — firewall, DNS, etc.
- **Spoke (per customer)**: each platform customer gets their own subscription
  and spoke network, peered to the hub. A customer's resources may span
  multiple resource groups.
- **Capability stacks (per customer)**: within a customer's spoke, each
  capability is its own stack.

## Repository layout

Each Pulumi project is self-contained: its own `Pulumi.yaml`, `pyproject.toml`,
`uv.lock` and `.venv`, living in a `project/` subdirectory. There is no
repo-root Python project or workspace.

```
projects/
  core/
    core-hub/project/     # hub network + shared services (the only project with code)
    data-hub/             # placeholder
  capabilities/           # per-customer capability stacks (placeholders)
    ai-search/
    databricks/
    sql-database/
  sopke/                  # per-customer spoke (placeholder; directory name is misspelled "spoke")
```

## Commands

Run from inside a project directory (e.g. `projects/core/core-hub/project`).
Pulumi is configured with the `uv` toolchain, so it manages the virtualenv
itself.

```sh
uv sync                        # install dependencies into .venv
uv add <package>               # add a dependency (never hand-edit uv.lock)
pulumi stack init <stack>      # no stacks are checked in yet
pulumi preview                 # show planned changes
pulumi up                      # deploy
```

Python `>=3.14` is required. There are no tests and no lint configuration yet;
`ruff format` / `ruff check --fix` run automatically on edited files via the
hooks in `.claude/settings.json` when `ruff` is installed.

## Conventions

### Resource naming

`Pulumi.yaml` sets `pulumi:autonaming` to `verbatim`: the logical name given
to a resource becomes its physical cloud name with no random suffix. Give
every resource a full, deliberate, collision-free name — and respect the
target resource type's naming rules (length, charset, global uniqueness).

### Pulumi multi-cloud components

Cloud infrastructure is organized as one `ComponentResource` per cloud per
capability, selected through a small factory. Follow this for every infra
capability (storage, networking, compute, etc.), even when only one cloud is
implemented today.

For a capability called `<thing>` (e.g. `storage`, `network`):

```
project/
  <thing>/
    __init__.py   # exports create_<thing>
    base.py       # <Thing> Protocol + <Thing>Args dataclass
    azure.py      # Azure<Thing>(ComponentResource)
    factory.py    # create_<thing>(cloud, name, args, opts)
```

- `base.py` is the cloud-agnostic contract: the `Protocol` declares only the
  outputs callers may rely on regardless of cloud, and the `Args` dataclass
  holds only cloud-neutral inputs. See
  `projects/core/core-hub/project/network/base.py` for the reference shape.
- Callers import `create_<thing>` from the package and never reference a
  cloud-specific class directly.

## Claude Code settings

`.claude/settings.json` blocks direct edits to lock files and denies
`git checkout main`, `git push --force`, and `rm -rf` — work on a branch.
