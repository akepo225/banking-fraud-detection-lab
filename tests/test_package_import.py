"""Tests for package-level imports and version."""

from banking_fraud_lab import (
    __version__,
    generate_learner_facing_minimal_banking_world,
    generate_minimal_banking_world,
)


def test_package_imports() -> None:
    """The package must expose the correct version and a callable generator."""
    assert __version__ == "0.1.0"
    assert callable(generate_minimal_banking_world)
    assert callable(generate_learner_facing_minimal_banking_world)
