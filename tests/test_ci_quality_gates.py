"""Tests that keep the v0.1 CI quality-gate coverage explicit."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
QUALITY_GATE_MANIFEST = REPO_ROOT / "docs" / "quality_gates" / "v0.1-ci.md"

REQUIRED_CI_COMMANDS = (
    "uv sync --extra dev",
    "uv run ruff check .",
    "uv run pytest",
)

QUALITY_GATE_TEST_IDS = {
    "tests/test_ci_quality_gates.py::test_ci_workflow_runs_clean_checkout_lint_and_full_python_tests",
    "tests/test_ci_quality_gates.py::test_quality_gate_manifest_maps_acceptance_criteria_to_existing_tests",
    "tests/test_ci_quality_gates.py::test_featured_notebook_smoke_tests_execute_nbconvert_targets",
    "tests/test_generator_determinism.py::test_minimal_world_is_deterministic_for_fixed_seed",
    "tests/test_generator_determinism.py::test_minimal_world_changes_for_different_seed",
    "tests/test_generator_entities.py::test_minimal_world_includes_required_v0_1_entities",
    "tests/test_generator_entities.py::test_minimal_world_preserves_referential_integrity",
    "tests/test_generator_entities.py::test_minimal_world_preserves_semantic_join_integrity",
    "tests/test_generator_entities.py::test_lifecycle_prevalence_uses_ranges_not_exact_row_outputs",
    "tests/test_private_banking_scenario.py::test_private_banking_scenario_prevalence_is_configurable",
    "tests/test_private_banking_scenario.py::test_private_banking_scenario_referential_integrity",
    "tests/test_digital_scam_to_mule_scenario.py::test_digital_scam_to_mule_prevalence_is_configurable",
    "tests/test_digital_scam_to_mule_scenario.py::test_digital_scam_to_mule_referential_integrity",
    "tests/test_schema_contract.py::test_schema_contract_column_names_match_generated_tables",
    "tests/test_schema_contract.py::test_schema_contract_type_families_match_generated_tables",
    "tests/test_schema_contract.py::test_schema_contract_is_documented_in_data_dictionary",
    "tests/test_sqlite_loader.py::test_generated_tables_can_be_loaded_into_sqlite_database",
    "tests/test_sqlite_loader.py::test_sqlite_schema_includes_core_foreign_key_relationships",
    "tests/test_sqlite_loader.py::test_representative_sql_examples_execute_successfully",
    "tests/test_case_library_metadata.py::test_case_source_packs_cover_v0_1_learning_areas",
    "tests/test_case_library_metadata.py::test_case_source_packs_have_required_metadata_and_sections",
    "tests/test_case_library_metadata.py::test_case_library_index_links_all_source_packs",
    "tests/test_regulatory_source_index.py::test_regulatory_index_declares_educational_non_advice_scope",
    "tests/test_regulatory_source_index.py::test_regulatory_notes_cover_required_source_families_and_official_links",
    "tests/test_regulatory_source_index.py::test_regulatory_notes_link_existing_exercises",
    "tests/test_foundations_notebook.py::test_foundations_notebook_executes",
    "tests/test_private_banking_notebook.py::test_private_banking_notebook_executes",
    "tests/test_digital_scam_to_mule_notebook.py::test_digital_scam_to_mule_notebook_executes",
    "tests/test_alert_governance_notebook.py::test_alert_governance_notebook_executes",
}

FEATURED_NOTEBOOK_TESTS = {
    "tests/test_foundations_notebook.py::test_foundations_notebook_executes": (
        "notebooks",
        "00_foundations",
        "foundations_data_tour.ipynb",
    ),
    "tests/test_private_banking_notebook.py::test_private_banking_notebook_executes": (
        "notebooks",
        "01_private_banking_transaction_fraud",
        "alpine_crest_baseline.ipynb",
    ),
    "tests/test_digital_scam_to_mule_notebook.py::test_digital_scam_to_mule_notebook_executes": (
        "notebooks",
        "02_digital_scam_to_mule",
        "novabank_scam_to_mule_baseline.ipynb",
    ),
    "tests/test_alert_governance_notebook.py::test_alert_governance_notebook_executes": (
        "notebooks",
        "03_alert_governance",
        "alert_governance_memo.ipynb",
    ),
}


def test_ci_workflow_runs_clean_checkout_lint_and_full_python_tests() -> None:
    """CI must install from a clean checkout, lint, and run the full pytest suite."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["test"]["steps"]

    assert any(str(step.get("uses", "")).startswith("actions/checkout@") for step in steps)
    assert any(str(step.get("uses", "")).startswith("astral-sh/setup-uv@") for step in steps)

    run_commands = tuple(step["run"].strip() for step in steps if "run" in step)
    assert run_commands == REQUIRED_CI_COMMANDS
    assert run_commands[-1] == "uv run pytest"
    assert _pytest_command_is_unfiltered(run_commands[-1])

    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    pytest_options = pyproject["tool"]["pytest"]["ini_options"]
    assert pytest_options["testpaths"] == ["tests"]


def test_quality_gate_manifest_maps_acceptance_criteria_to_existing_tests() -> None:
    """The v0.1 gate manifest must cite existing tests that CI runs through pytest."""
    manifest = QUALITY_GATE_MANIFEST.read_text(encoding="utf-8")
    defined_test_ids = _defined_test_ids()

    for command in REQUIRED_CI_COMMANDS:
        assert f"`{command}`" in manifest

    missing_tests = sorted(QUALITY_GATE_TEST_IDS - defined_test_ids)
    assert not missing_tests, f"Quality-gate manifest references missing tests: {missing_tests}"

    missing_manifest_entries = sorted(
        test_id for test_id in QUALITY_GATE_TEST_IDS if f"`{test_id}`" not in manifest
    )
    assert not missing_manifest_entries, (
        "docs/quality_gates/v0.1-ci.md must list every required quality-gate test: "
        f"{missing_manifest_entries}"
    )


def test_featured_notebook_smoke_tests_execute_nbconvert_targets() -> None:
    """Featured v0.1 notebook smoke tests must execute the expected notebooks."""
    for test_id, notebook_parts in FEATURED_NOTEBOOK_TESTS.items():
        test_path_text, test_name = test_id.split("::", maxsplit=1)
        test_path = REPO_ROOT / Path(test_path_text)
        test_text = test_path.read_text(encoding="utf-8")

        assert f"def {test_name}(" in test_text
        assert "nbconvert" in test_text
        assert "--execute" in test_text
        for notebook_part in notebook_parts:
            assert notebook_part in test_text


def _defined_test_ids() -> set[str]:
    """Return normalized pytest-style ids for all test functions in tests/."""
    test_ids: set[str] = set()
    for test_path in sorted((REPO_ROOT / "tests").glob("test_*.py")):
        relative_path = test_path.relative_to(REPO_ROOT).as_posix()
        text = test_path.read_text(encoding="utf-8")
        for match in re.finditer(r"^def (test_[A-Za-z0-9_]+)\(", text, flags=re.MULTILINE):
            test_ids.add(f"{relative_path}::{match.group(1)}")
    return test_ids


def _pytest_command_is_unfiltered(pytest_command: str) -> bool:
    """Return whether the CI pytest command avoids selectors that would skip gate tests."""
    forbidden_selectors = (" -k ", " -m ", " --ignore", " --deselect", " tests/")
    command = f" {pytest_command} "
    return all(selector not in command for selector in forbidden_selectors)
