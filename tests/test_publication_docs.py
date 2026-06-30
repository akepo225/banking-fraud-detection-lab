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


# --- v0.9 terminology guardrails (issue #232) -------------------------------
# Extend publication-docs coverage to the capstone and beta surface. Mirrors the
# prohibition vocabulary already enforced by the case-library / regulatory-index
# validators (CRLF-tolerant, whitespace-aware) without weakening them.

V09_TERMINOLOGY_DOC_PATHS = (
    "docs/capstone/alpine_crest_brief.md",
    "docs/capstone/novabank_brief.md",
    "docs/capstone/rubric.md",
    "docs/capstone/presentation_template.md",
    "docs/capstone/troubleshooting.md",
    "docs/release/v0.9-beta-checklist.md",
)

# Real-bank names that must never appear in public-facing text. Word-bounded so
# "substrate" (contains "ubs") does not trip.
FORBIDDEN_REAL_BANK_NAMES = (
    "julius baer",
    "ubs ",
    "credit suisse",
    "hsbc",
    "barclays",
    "deutsche bank",
    "santander",
)

# Job-preparation / public-release framing that has no place in the curriculum.
FORBIDDEN_JOB_OR_RELEASE_FRAMING = (
    "portfolio project",
    "recruiters",
    "job-preparation",
    "we shipped",
    "publicly released",
    "is now published",
    "has been published",
)

# Imperative compliance/legal-advice wording (mirrors case-library ban).
FORBIDDEN_IMPERATIVE_COMPLIANCE = (
    "you must comply",
    "must comply with",
    "must report",
    "required to comply",
    "legal requirement for learners",
)

# Reconstruction claims (mirrors case-library BANNED_RECONSTRUCTION_PHRASES).
FORBIDDEN_RECONSTRUCTION_CLAIMS = (
    "reconstructs the",
    "reproduces the",
    "recreation of",
    "based on actual",
    "replicate the",
    "exact case",
)


def _v09_doc_texts() -> dict[str, str]:
    """Read every v0.9 public-facing doc into a normalized lower-case form."""
    return {
        path: _read(path).lower()
        for path in V09_TERMINOLOGY_DOC_PATHS
        if (ROOT / path).exists()
    }


def test_v09_docs_avoid_forbidden_real_bank_names() -> None:
    """No v0.9 public-facing doc names a real bank."""
    for path, text in _v09_doc_texts().items():
        for bank in FORBIDDEN_REAL_BANK_NAMES:
            assert bank not in text, f"{path} names a real bank: {bank!r}"


def test_v09_docs_avoid_job_preparation_and_public_release_framing() -> None:
    """No v0.9 public-facing doc uses job-prep or public-release framing."""
    for path, text in _v09_doc_texts().items():
        for phrase in FORBIDDEN_JOB_OR_RELEASE_FRAMING:
            assert phrase not in text, f"{path} uses banned framing: {phrase!r}"


def test_v09_docs_avoid_imperative_compliance_wording() -> None:
    """No v0.9 public-facing doc issues imperative legal/compliance instructions."""
    for path, text in _v09_doc_texts().items():
        for phrase in FORBIDDEN_IMPERATIVE_COMPLIANCE:
            assert phrase not in text, f"{path} uses imperative compliance: {phrase!r}"


def test_v09_docs_avoid_real_event_reconstruction_claims() -> None:
    """No v0.9 public-facing doc claims to reconstruct/reproduce a real event."""
    for path, text in _v09_doc_texts().items():
        for phrase in FORBIDDEN_RECONSTRUCTION_CLAIMS:
            assert phrase not in text, f"{path} makes a reconstruction claim: {phrase!r}"


def test_v09_docs_use_fixed_glossary_institutions() -> None:
    """v0.9 docs use the fixed institution names, not synonyms or real banks."""
    alpine_crest_brief = _read("docs/capstone/alpine_crest_brief.md")
    novabank_brief = _read("docs/capstone/novabank_brief.md")
    assert "Alpine Crest Private Bank" in alpine_crest_brief
    assert "NovaBank Digital" in novabank_brief


def test_v09_capstone_notebooks_avoid_forbidden_framing() -> None:
    """The committed capstone notebooks avoid prohibited public-facing framing.

    Reads the notebook JSON as text (CRLF/whitespace-tolerant) and checks the
    prohibition vocabulary, mirroring the case-library/regex guardrails.
    """
    notebook_dir = ROOT / "notebooks" / "09_capstone"
    notebooks = sorted(notebook_dir.glob("*.ipynb"))
    assert notebooks, "expected committed capstone notebooks"
    forbidden = (
        FORBIDDEN_REAL_BANK_NAMES
        + FORBIDDEN_JOB_OR_RELEASE_FRAMING
        + FORBIDDEN_IMPERATIVE_COMPLIANCE
        + FORBIDDEN_RECONSTRUCTION_CLAIMS
    )
    for notebook in notebooks:
        text = notebook.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, f"{notebook.name} contains banned phrase: {phrase!r}"


def test_v09_customer_term_is_only_used_to_define_the_glossary() -> None:
    """The word 'customer' may appear only in the glossary-definition context.

    The glossary explicitly defines Client as 'the legal customer' and says
    'Never customer'. A bare-term ban would fail on that definition, so instead
    assert 'customer' appears only alongside the glossary markers ('client' or
    'never'), catching any NEW assertive use while keeping the anti-term valid.
    """
    paths = V09_TERMINOLOGY_DOC_PATHS + ("notebooks/09_capstone/README.md",)
    for path in paths:
        full = ROOT / path
        if not full.exists():
            continue
        for line in full.read_text(encoding="utf-8").splitlines():
            if "customer" not in line.lower():
                continue
            joined = _normalize(line).lower()
            assert "client" in joined or "never" in joined, (
                f"{path} uses 'customer' outside the glossary definition: {line.strip()!r}"
            )


# --- v1.0 terminology guardrails + extension boundary (issue #253) -----------
# Extend publication-docs coverage to the v1.0 release surface and add a
# structural extension-boundary guardrail. The terminology checks reuse the
# FORBIDDEN_* vocabulary already enforced on the v0.9 surface; the extension-
# boundary guard keeps v1.1-v1.4 out of the v1.0 core.
#
# The v1.0 acceptance review doc is intentionally excluded from the FLAT
# forbidden-substring checks below (mirrors v0.9, where the review doc is also
# excluded): the review legitimately lists the banned phrases inside its
# prohibited-content search command and quotes the ROADMAP criterion. The review
# is instead covered line-by-line by
# tests/test_v10_acceptance_review.py::test_v10_acceptance_review_preserves_private_pre_publication_framing
# (which skips the rg command and code fences) and by the content-assertion
# tests. The scope doc and the release checklist (#255) are both clean of every
# forbidden substring, so they stay in.

V10_TERMINOLOGY_DOC_PATHS = (
    "docs/release/v1.0-scope.md",
    "docs/release/v1.0-release-checklist.md",
)


def _v10_doc_texts() -> dict[str, str]:
    """Read every v1.0 public-facing doc into a normalized lower-case form."""
    return {
        path: _read(path).lower()
        for path in V10_TERMINOLOGY_DOC_PATHS
        if (ROOT / path).exists()
    }


def test_v10_docs_avoid_forbidden_real_bank_names() -> None:
    """No v1.0 public-facing doc names a real bank."""
    for path, text in _v10_doc_texts().items():
        for bank in FORBIDDEN_REAL_BANK_NAMES:
            assert bank not in text, f"{path} names a real bank: {bank!r}"


def test_v10_docs_avoid_job_preparation_and_public_release_framing() -> None:
    """No v1.0 public-facing doc uses job-prep or public-release framing."""
    for path, text in _v10_doc_texts().items():
        for phrase in FORBIDDEN_JOB_OR_RELEASE_FRAMING:
            assert phrase not in text, f"{path} uses banned framing: {phrase!r}"


def test_v10_docs_avoid_imperative_compliance_wording() -> None:
    """No v1.0 public-facing doc issues imperative legal/compliance instructions."""
    for path, text in _v10_doc_texts().items():
        for phrase in FORBIDDEN_IMPERATIVE_COMPLIANCE:
            assert phrase not in text, f"{path} uses imperative compliance: {phrase!r}"


def test_v10_docs_avoid_real_event_reconstruction_claims() -> None:
    """No v1.0 public-facing doc claims to reconstruct/reproduce a real event."""
    for path, text in _v10_doc_texts().items():
        for phrase in FORBIDDEN_RECONSTRUCTION_CLAIMS:
            assert phrase not in text, f"{path} makes a reconstruction claim: {phrase!r}"


def test_v10_docs_use_fixed_glossary_institutions() -> None:
    """v1.0 docs use the fixed institution names, not synonyms or real banks."""
    review = _read("docs/release/v1.0-complete-public-core-curriculum-acceptance-review.md")
    assert "Alpine Crest Private Bank" in review
    assert "NovaBank Digital" in review


def test_v10_customer_term_is_only_used_to_define_the_glossary() -> None:
    """In v1.0 docs the word 'customer' may appear only in the glossary context."""
    for path in V10_TERMINOLOGY_DOC_PATHS:
        full = ROOT / path
        if not full.exists():
            continue
        for line in full.read_text(encoding="utf-8").splitlines():
            if "customer" not in line.lower():
                continue
            joined = _normalize(line).lower()
            assert "client" in joined or "never" in joined, (
                f"{path} uses 'customer' outside the glossary definition: {line.strip()!r}"
            )


# v1.1-v1.4 advanced-track phrases that have no legitimate place in the v1.0
# core public narrative (README). Kept deliberately to unambiguous track terms;
# the structural freeze below is the primary boundary guard, because some generic
# tokens (e.g. the v0.6 optional Neo4j extra, monitoring "no Kafka" disclaimers,
# the glossary's "digital brokerages") legitimately appear elsewhere in core.
V10_README_ADVANCED_TRACK_PHRASES = (
    "wallet withdrawal",
    "on-ramp",
    "off-ramp",
    "market abuse",
    "market-abuse",
    "unauthorized trading",
    "order execution",
    "communication monitoring",
    "insider risk",
    "insider-risk",
    "case-note summarization",
    "case-note",
    "stream processing",
    "stream-processing",
    "api deployment",
    "relational database deploy",
)


def test_v10_core_module_dirs_stay_within_frozen_core_range() -> None:
    """No notebook module directory beyond the frozen 00-09 core may exist.

    The primary v1.1-v1.4 extension-boundary guard: v1.0 is frozen at the ten
    modules 00_foundations through 09_capstone (docs/release/v1.0-scope.md). A
    new v1.1+ track would land as a ``notebooks/10_*`` (or higher) directory, so
    this structural check catches leakage that a keyword scan cannot.
    """
    numbered = [
        path
        for path in (ROOT / "notebooks").iterdir()
        if path.is_dir() and re.fullmatch(r"[0-9][0-9]_.*", path.name)
    ]
    assert numbered, "expected numbered notebook module directories"
    for module in numbered:
        assert int(module.name[:2]) <= 9, (
            f"v1.0 core is frozen at 00-09; found module beyond core: {module.name}"
        )


def test_v10_extension_boundary_is_recorded() -> None:
    """The v1.1-v1.4 boundary is on record in ADR-0004, ROADMAP, and the scope doc."""
    assert (
        ROOT / "docs" / "adr" / "0004-treat-v1-1-through-v1-4-as-optional-advanced-extensions.md"
    ).is_file()
    roadmap = _read("docs/ROADMAP.md")
    assert "## Post-1.0 Advanced Tracks" in roadmap
    assert "v1.1" in roadmap
    assert "v1.4" in roadmap
    scope = _read("docs/release/v1.0-scope.md")
    assert "v1.1" in scope
    assert "v1.4" in scope


def test_v10_readme_keeps_advanced_tracks_out_of_core_narrative() -> None:
    """The public README must not introduce v1.1-v1.4 advanced tracks as core.

    README is the public entry narrative; it stays pure v1.0. v1.1-v1.4 tracks
    are confined to docs/ROADMAP.md § Post-1.0 and docs/adr/0004-*.md (asserted
    present above) plus the scope/review docs that document the boundary.
    """
    readme = _read("README.md").lower()
    for phrase in V10_README_ADVANCED_TRACK_PHRASES:
        assert phrase not in readme, f"README introduces advanced-track term: {phrase!r}"


# --- v1.0 framing-document consistency (issue #251) -------------------------
# Reuses the test_readme_markdown_links_resolve idiom across the framing docs and
# reconciles the module-06 naming drift recorded in docs/release/v1.0-scope.md.

V10_FRAMING_DOC_PATHS = (
    "README.md",
    "docs/ROADMAP.md",
    "CONTRIBUTING.md",
)


def _doc_local_link_targets(doc_rel: str) -> list[str]:
    """Return local (non-http/fragment/mailto) markdown link targets in one doc."""
    text = _read(doc_rel)
    targets = re.findall(r"\]\(([^)]+)\)", text)
    resolved: list[str] = []
    for target in targets:
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path_part = target.split()[0].split("#", 1)[0]
        if path_part:
            resolved.append(path_part)
    return resolved


def test_v10_framing_doc_local_links_resolve() -> None:
    """Every local markdown link in the framing docs must resolve to an existing file.

    Reuses the test_readme_markdown_links_resolve idiom across README, ROADMAP,
    CONTRIBUTING, every ADR, and every release doc. External, fragment, and mailto
    targets are skipped; links resolve relative to the doc's directory or the repo
    root. Guards against dead links to notebooks or docs renamed or moved.
    """
    docs = list(V10_FRAMING_DOC_PATHS)
    docs += sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "docs" / "adr").glob("*.md"))
    docs += sorted(
        path.relative_to(ROOT).as_posix() for path in (ROOT / "docs" / "release").glob("*.md")
    )
    unresolved: list[str] = []
    for doc_rel in docs:
        doc_dir = (ROOT / doc_rel).parent
        for target in _doc_local_link_targets(doc_rel):
            if (doc_dir / target).exists() or (ROOT / target).exists():
                continue
            unresolved.append(f"{doc_rel} -> {target}")
    assert not unresolved, f"framing docs have unresolved local links: {unresolved}"


def test_v10_release_docs_reachable_from_roadmap() -> None:
    """The v1.0 scope doc and acceptance review must be reachable from ROADMAP."""
    roadmap = _read("docs/ROADMAP.md")
    assert "(release/v1.0-scope.md)" in roadmap
    assert "(release/v1.0-complete-public-core-curriculum-acceptance-review.md)" in roadmap


def test_v10_roadmap_required_modules_match_on_disk() -> None:
    """ROADMAP's v1.0 required-module names must equal the on-disk module directories.

    Closes the module-06 naming drift (docs/release/v1.0-scope.md § Naming-
    discrepancy note): ROADMAP listed 06_graph_network_analytics while the on-disk
    directory is 06_graph_network_fraud. Both must now match exactly.
    """
    text = _read("docs/ROADMAP.md")
    start = text.index("### v1.0: Complete Public Core Curriculum")
    rest = text[start:]
    modules_block = rest.split("v1.0 acceptance criteria:")[0]
    roadmap_modules = re.findall(r"`([0-9][0-9]_[a-z_]+)`", modules_block)
    on_disk = sorted(
        path.name
        for path in (ROOT / "notebooks").iterdir()
        if path.is_dir() and re.fullmatch(r"[0-9][0-9]_.*", path.name)
    )
    assert sorted(roadmap_modules) == on_disk, (
        f"ROADMAP v1.0 required modules {sorted(roadmap_modules)} != on-disk {on_disk}"
    )

