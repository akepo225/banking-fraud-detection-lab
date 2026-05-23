from banking_fraud_lab import __version__, generate_minimal_banking_world


def test_package_imports() -> None:
    assert __version__ == "0.1.0"
    assert callable(generate_minimal_banking_world)
