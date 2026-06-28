import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.split())


def test_readme_covers_publication_readiness_contract() -> None:
    readme = _normalize(_read("README.md"))

    required_terms = [
        "Private pre-publication curriculum",
        "Target learner",
        "Fraud detection tracks",
        "Private-banking fraud detection",
        "Digital-banking fraud detection",
        "Alpine Crest Private Bank",
        "NovaBank Digital",
        "educational only",
        "unaffiliated",
        "does not use real client data",
        "does not reconstruct real events",
        "does not provide legal, compliance, audit, investment, regulatory, or professional advice",
        "uv sync --extra dev",
        "uv run ruff check .",
        "uv run pytest",
        "uv run python -m banking_fraud_lab.create_sqlite data/sample/minimal_world.sqlite",
        "works in Bash and PowerShell",
        "uv run python -c",
    ]
    for term in required_terms:
        assert term in readme

    required_links = [
        "(docs/schema/README.md)",
        "(docs/schema/data_dictionary.md)",
        "(notebooks/00_foundations/warmups/)",
        "(sql/README.md)",
        "(docs/evaluation/metrics.md)",
        "(docs/cases/index.md)",
        "(docs/regulation/index.md)",
        "(docs/quality_gates/v0.1-ci.md)",
        "(docs/ROADMAP.md)",
        "(docs/adr/0001-broaden-scope-to-banking-fraud-detection-lab.md)",
        "(CONTRIBUTING.md)",
        "(docs/release/v0.1-publication-checklist.md)",
        "(docs/release/v0.5-acceptance-review.md)",
        "(notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb)",
        "(notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb)",
        "(LICENSE.md)",
    ]
    for link in required_links:
        assert link in readme


def test_license_documents_explain_split_scope_and_boundaries() -> None:
    license_index = _normalize(_read("LICENSE.md"))
    code_license = _normalize(_read("LICENSES/CODE-MIT.md"))
    content_license = _normalize(_read("LICENSES/CONTENT-CC-BY-NC-4.0.md"))

    assert "Code in `src/`, `tests/`, and `sql/` is licensed under the MIT License" in license_index
    assert (
        "Educational content in `README.md`, `CONTEXT.md`, `docs/`, `notebooks/`, "
        "and `data/sample/` is licensed under Creative Commons Attribution-NonCommercial 4.0"
        in license_index
    )
    assert "This license applies to code in `src/`, `tests/`, and `sql/`." in code_license
    assert "MIT License" in code_license
    assert "This covers `README.md`, `CONTEXT.md`, `docs/`, `notebooks/`, and" in content_license
    assert "`data/sample/`." in content_license
    assert "non-commercial purposes with attribution" in content_license
    assert "unaffiliated" in content_license
    assert "does not reconstruct real events" in content_license
    assert "does not provide legal, compliance, audit," in content_license


def test_publication_checklist_reflects_v0_1_prd_gate() -> None:
    checklist = _normalize(_read("docs/release/v0.1-publication-checklist.md"))

    assert "<!-- HITL-REVIEW-REQUIRED:" in checklist
    assert "repository remains private until the v0.1 publication gate is accepted" in checklist
    assert "educational only and unaffiliated" in checklist
    assert "synthetic data only" in checklist
    assert "does not claim to reconstruct real events" in checklist
    assert "does not provide legal, compliance, audit, investment," in checklist

    required_gates = [
        "Private pre-publication posture",
        "No personal job-preparation material or real client data",
        "README, disclaimer, split licensing, ADR, and contribution guidance",
        "Realistic synthetic data model and data dictionary",
        "Deterministic generator and sample data",
        "SQLite loader supports first SQL exercises",
        "Featured notebooks run end-to-end on tiny data",
        "Seeded case library and regulatory source index",
        "Tests cover v0.1 quality gates",
        "Lightweight CI runs linting and tests",
    ]
    for gate in required_gates:
        assert gate in checklist


def test_public_facing_docs_avoid_personal_or_real_bank_framing() -> None:
    docs = {
        "README.md": _read("README.md"),
        "data/sample/README.md": _read("data/sample/README.md"),
        "docs/ROADMAP.md": _read("docs/ROADMAP.md"),
        "docs/release/v0.1-publication-checklist.md": _read(
            "docs/release/v0.1-publication-checklist.md"
        ),
    }

    for path, text in docs.items():
        assert "Julius Baer" not in text, path
        assert "job-preparation repo" not in text, path
        assert "portfolio project" not in text, path
        assert "Portfolio presentation" not in text, path
        assert "recruiters" not in text, path

    assert "pre-publication" in docs["README.md"]
    assert "pre-publication" in docs["docs/release/v0.1-publication-checklist.md"]

    readme = docs["README.md"]
    assert "create_sqlite data/sample banking_fraud_lab.sqlite" not in readme
    assert "create_sqlite data/sample/minimal_world.sqlite" in readme
    assert "<<'PY'" not in readme
    assert "<<'PY'" not in docs["data/sample/README.md"]

    audit = _read("docs/release/v0.1-publication-gate-audit.md")
    assert "README SQLite command used two positional arguments" in audit
    assert "Future roadmap wording used personal/job-market framing" in audit
    assert "described the project as a public curriculum repository" in audit
    assert "Data-model consistency review found no schema/sample/foreign-key" in audit
    assert "| Prohibited-content search (see command below) | Reviewed |" in audit
    command_blocks = re.findall(r"```(?:bash|shell)\n(.*?)```", audit, flags=re.DOTALL)
    assert any("rg -n -i" in block for block in command_blocks), command_blocks

    context = _read("CONTEXT.md")
    assert "The public curriculum repository" not in context
    assert "pre-publication curriculum repository" in context


def test_notebook_and_sql_guides_are_actionable_for_end_users() -> None:
    notebook_guide = _normalize(_read("notebooks/README.md"))
    sql_guide = _normalize(_read("sql/README.md"))
    audit = _read("docs/release/v0.1-publication-gate-audit.md")

    notebook_terms = [
        "uv sync --extra dev",
        "uv run jupyter lab notebooks",
        "uv run pytest tests/test_foundations_notebook.py tests/test_private_banking_notebook.py tests/test_digital_scam_to_mule_notebook.py tests/test_alert_governance_notebook.py",
    ]
    for term in notebook_terms:
        assert term in notebook_guide

    warmup_terms = [
        "Optional Warm-Ups",
        "outside the required core module sequence",
        "00_foundations/warmups/python_canonical_data_warmup.ipynb",
        "00_foundations/warmups/pandas_progressive_views_warmup.ipynb",
        "00_foundations/warmups/sql_progressive_views_warmup.ipynb",
        "00_foundations/warmups/sklearn_alert_scoring_warmup.ipynb",
        "uv run pytest tests/test_warmup_notebooks.py",
    ]
    for term in warmup_terms:
        assert term in notebook_guide

    sql_terms = [
        "uv run python -m banking_fraud_lab.run_sql data/sample/minimal_world.sqlite sql/examples/04_progressive_alert_queue.sql",
        "does not require a separate `sqlite3` command-line install",
        'sqlite3 data/sample/minimal_world.sqlite ".read sql/examples/04_progressive_alert_queue.sql"',
        "uv run pytest tests/test_sqlite_loader.py::test_representative_sql_examples_execute_successfully",
    ]
    for term in sql_terms:
        assert term in sql_guide

    assert "did not tell a new user how to launch" in audit
    assert "listed optional `warmups/` material" in audit
    assert "did not show how to run them against the generated database" in audit


def test_readme_curriculum_map_covers_every_module_directory() -> None:
    """Every numbered notebook module on disk must be linked from the README.

    Guards against a module directory being added under ``notebooks/`` without a
    corresponding entry in the README Curriculum Map, which is how the v0.4
    modules 04 and 05 originally went undocumented.
    """
    readme = _read("README.md")

    module_dirs = sorted(path.name for path in (ROOT / "notebooks").iterdir() if path.is_dir())
    numbered_modules = [name for name in module_dirs if re.fullmatch(r"[0-9][0-9]_.*", name)]
    assert numbered_modules, "expected at least one numbered notebook module directory"

    missing = [
        name for name in numbered_modules if f"(notebooks/{name}/" not in readme
    ]
    assert not missing, (
        "README Curriculum Map is missing links for module directories: "
        f"{missing}. Every notebooks/[0-9][0-9]_* directory must be linked."
    )


def test_readme_markdown_links_resolve() -> None:
    """Every local markdown link in the README must resolve to an existing path.

    External (http/https), fragment (#), and mailto targets are skipped. Guards
    against dead links to notebooks or docs that were renamed or moved.
    """
    readme = _read("README.md")
    targets = re.findall(r"\]\(([^)]+)\)", readme)

    unresolved = []
    for target in targets:
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # Markdown links may carry an optional title fragment: ``path "title"``.
        path_part = target.split()[0]
        if not (ROOT / path_part).exists():
            unresolved.append(target)
    assert not unresolved, f"README links do not resolve to existing files: {unresolved}"


def test_capstone_is_reachable_from_entry_docs() -> None:
    """The v0.9 capstone must be reachable from README, notebook guide, and SQL guide.

    Closes issue #230 cross-doc consistency: a first-time reader of the README,
    notebook guide, or SQL guide must be able to reach the capstone module and
    its scenario briefs without dead links. ``test_readme_markdown_links_resolve``
    already guarantees the README links themselves resolve.
    """
    readme = _read("README.md")
    notebook_guide = _read("notebooks/README.md")
    sql_guide = _read("sql/README.md")

    # README curriculum map links the 09_capstone module and docs/capstone/.
    assert "(notebooks/09_capstone/" in readme
    assert "(docs/capstone/)" in readme
    # Notebook guide documents the 09_capstone module and its README.
    assert "`09_capstone/`" in notebook_guide
    assert "(09_capstone/README.md)" in notebook_guide
    # SQL guide links the capstone SQL examples.
    assert re.search(r"\]\(([^)]+12_capstone_private_banking\.sql)\)", sql_guide)
    assert re.search(r"\]\(([^)]+13_capstone_digital_banking\.sql)\)", sql_guide)


def test_capstone_scenario_briefs_link_back_to_curriculum() -> None:
    """Each capstone brief links the notebook module and SQL example it frames."""
    capstone_dir = ROOT / "docs" / "capstone"
    briefs = {
        "alpine_crest_brief.md": (
            "notebooks/09_capstone/",
            "12_capstone_private_banking.sql",
        ),
        "novabank_brief.md": (
            "notebooks/09_capstone/",
            "13_capstone_digital_banking.sql",
        ),
    }
    for filename, (notebook_link, sql_example) in briefs.items():
        text = (capstone_dir / filename).read_text(encoding="utf-8")
        assert re.search(rf"\]\(([^)]+{re.escape(notebook_link)})\)", text), (
            f"{filename} does not link {notebook_link}"
        )
        assert re.search(rf"\]\(([^)]+{re.escape(sql_example)})\)", text), (
            f"{filename} does not link {sql_example}"
        )


def test_capstone_notebook_guide_markdown_links_resolve() -> None:
    """Every local markdown link in the notebook guide must resolve."""
    guide = _read("notebooks/README.md")
    targets = re.findall(r"\]\(([^)]+)\)", guide)
    unresolved = []
    for target in targets:
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path_part = target.split()[0].split("#", 1)[0]
        if not path_part:
            continue
        resolved = ROOT / "notebooks" / path_part
        if not resolved.exists():
            unresolved.append(target)
    assert not unresolved, f"notebook guide links do not resolve: {unresolved}"
