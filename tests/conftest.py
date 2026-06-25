"""Shared pytest fixtures for graph and downstream v0.6 slices."""

from __future__ import annotations

from collections.abc import Iterator

import networkx as nx
import pandas as pd
import pytest

from banking_fraud_lab import build_banking_graph, generate_minimal_banking_world


@pytest.fixture
def tiny_banking_tables() -> dict[str, pd.DataFrame]:
    """Seed-42 tiny canonical generated tables, reused across graph tests."""
    return generate_minimal_banking_world(seed=42, scale="tiny")


@pytest.fixture
def tiny_banking_graph(
    tiny_banking_tables: dict[str, pd.DataFrame],
) -> nx.MultiDiGraph:
    """A deterministic tiny graph built from the seed-42 tiny tables."""
    return build_banking_graph(tiny_banking_tables)


@pytest.fixture
def tiny_graph_tables(
    tiny_banking_tables: dict[str, pd.DataFrame],
) -> Iterator[tuple[nx.MultiDiGraph, dict[str, pd.DataFrame]]]:
    """Yield the tiny graph and its source tables together for join-style tests."""
    yield build_banking_graph(tiny_banking_tables), tiny_banking_tables
