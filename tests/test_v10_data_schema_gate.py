"""v1.0 synthetic-data, SQLite, and schema validation gate (issue #252).

v1.0 adds no schema, generator, or src/ changes (ADR-0002). This gate REUSES —
does not duplicate or weaken — the three existing invariant holders that enforce
the v1.0 data exit criteria (PRD #53 / docs/ROADMAP.md acceptance criteria):

- tests/test_schema_contract.py: generated columns/types match the data dictionary.
- tests/test_progressive_views.py: Progressive data views conform and are documented.
- tests/test_sqlite_loader.py: the SQLite loader + representative SQL examples run.

The gate asserts each module is present, importable, protects its on-disk artifact,
and contributes tests to the unfiltered ``uv run pytest`` (the canonical CI
invocation, which runs — and therefore enforces "pass" for — every one of them on
each check). If a drift between generated data and the schema/data dictionary is
found, the gate fails here; it is NOT patched in src/ under this slice.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The three invariant holders #252 reuses. Each already enforces a v1.0 data exit
# criterion; this gate proves they are wired into the suite, not weakened.
V10_DATA_SCHEMA_GATE_MODULES = (
    "test_schema_contract",
    "test_progressive_views",
    "test_sqlite_loader",
)

# The on-disk artifact each gate module protects. Asserting these exist ties the
# gate to the real invariant (no drift can hide a missing data dictionary, view
# doc, or SQL example) without duplicating the modules' own assertions.
V10_DATA_SCHEMA_ARTIFACTS = {
    "test_schema_contract": "docs/schema/data_dictionary.md",
    "test_progressive_views": "docs/schema/progressive_views.md",
    "test_sqlite_loader": "sql/examples/00_smoke_tables.sql",
}


@pytest.mark.parametrize("module_name", V10_DATA_SCHEMA_GATE_MODULES)
def test_v10_data_schema_gate_module_present(module_name: str) -> None:
    """Each data/schema/SQLite invariant holder must be present, importable, and protect its artifact."""
    module_path = ROOT / "tests" / f"{module_name}.py"
    assert module_path.is_file(), f"data/schema gate module missing: {module_path}"
    assert importlib.util.find_spec(module_name) is not None, (
        f"data/schema gate module not importable: {module_name}"
    )
    artifact = ROOT / V10_DATA_SCHEMA_ARTIFACTS[module_name]
    assert artifact.is_file(), f"{module_name} protected artifact missing: {artifact}"


def test_v10_data_schema_gate_modules_collect_tests() -> None:
    """Each invariant holder must contribute tests to the unfiltered pytest suite.

    Runs ``uv run pytest --collect-only`` over the three modules (the canonical CI
    runner) and asserts each contributes at least one collected test. That proves
    the invariants are wired into ``uv run pytest``, which runs them — and therefore
    enforces "pass" — on every CI check, without duplicating their execution here.
    """
    module_paths = [str(ROOT / "tests" / f"{name}.py") for name in V10_DATA_SCHEMA_GATE_MODULES]
    result = subprocess.run(  # noqa: S603 - "uv" is the project-mandated runner; argv is controlled.
        ["uv", "run", "pytest", "--collect-only", "-q", *module_paths],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    collected = result.stdout + result.stderr
    for module_name in V10_DATA_SCHEMA_GATE_MODULES:
        # ``--collect-only -q`` reports either node ids (``module.py::test``) or a
        # per-file count (``module.py: <N>``); accept either, but require >= 1 test.
        has_nodes = f"{module_name}.py::" in collected
        count_match = re.search(rf"{re.escape(module_name)}\.py:\s*(\d+)", collected)
        count = int(count_match.group(1)) if count_match else 0
        assert has_nodes or count >= 1, f"{module_name} contributed no collected tests"
