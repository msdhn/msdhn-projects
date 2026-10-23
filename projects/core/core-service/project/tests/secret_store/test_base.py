from secret_store import KeyVaultArgs


def test_key_vault_args_default_to_empty():
    args = KeyVaultArgs()

    assert args.tags == {}
    assert args.allowed_subnet_ids == []
    assert args.role_assignments == {}


def test_key_vault_args_defaults_are_not_shared_between_instances():
    first = KeyVaultArgs()
    first.tags["owner"] = "core-team"
    first.allowed_subnet_ids.append("subnet-id")

    second = KeyVaultArgs()

    assert second.tags == {}
    assert second.allowed_subnet_ids == []
