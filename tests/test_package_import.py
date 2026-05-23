"""Tests for package-level imports and version."""

from banking_fraud_lab import (
    __version__,
    build_learner_facing_views,
    create_minimal_banking_world_sqlite,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
    load_tables_to_sqlite,
)


def test_package_imports() -> None:
    """The package must expose the correct version and a callable generator."""
    assert __version__ == "0.1.0"
    assert callable(generate_minimal_banking_world)
    assert callable(build_learner_facing_views)
    assert callable(generate_learner_facing_minimal_banking_world)
    assert callable(create_minimal_banking_world_sqlite)
    assert callable(load_tables_to_sqlite)
