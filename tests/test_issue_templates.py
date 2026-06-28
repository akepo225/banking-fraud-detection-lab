"""Contract tests for the public issue templates and contributor guidance (#233).

Mirrors the v0.9 docs-contract pattern: asserts the issue templates exist, parse
as YAML GitHub issue forms, reference the repo's fixed triage-label vocabulary,
and that the expanded CONTRIBUTING keeps the public-facing boundaries.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / ".github" / "ISSUE_TEMPLATE"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"

# Fixed triage-label vocabulary (docs/agents/triage-labels.md).
CATEGORY_LABELS = {"bug", "enhancement"}
STATE_LABELS = {
    "needs-triage",
    "needs-info",
    "ready-for-agent",
    "ready-for-human",
    "wontfix",
}
KNOWN_LABELS = CATEGORY_LABELS | STATE_LABELS | {"afk", "hitl", "blocked", "parent"}


def _templates() -> dict[str, dict[str, object]]:
    """Return parsed issue-form templates keyed by filename stem.

    ``config.yml`` is a template-directory config (not an issue form), so it is
    excluded from the form-template set.
    """
    templates: dict[str, dict[str, object]] = {}
    for path in sorted(TEMPLATE_DIR.glob("*.yml")):
        if path.name == "config.yml":
            continue
        templates[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return templates


def test_issue_templates_present() -> None:
    """At least bug and enhancement templates exist under .github/ISSUE_TEMPLATE/."""
    assert TEMPLATE_DIR.is_dir(), f"{TEMPLATE_DIR} does not exist"
    templates = _templates()
    assert "bug_report" in templates, "missing bug report template"
    assert "enhancement" in templates, "missing enhancement template"


def test_config_disables_blank_issues_for_structured_intake() -> None:
    """config.yml should disable blank issues so public feedback uses the forms."""
    config_path = TEMPLATE_DIR / "config.yml"
    assert config_path.is_file(), ".github/ISSUE_TEMPLATE/config.yml missing"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert isinstance(config, dict)
    assert config.get("blank_issues_enabled") is False, (
        "blank_issues_enabled must be false so reporters use the structured forms"
    )


def test_issue_templates_parse_and_reference_known_labels() -> None:
    """Each template is a valid YAML issue form whose labels are in the repo vocabulary."""
    templates = _templates()
    assert templates, "no issue templates found"
    for stem, data in templates.items():
        assert isinstance(data, dict), f"{stem} did not parse to a mapping"
        for required_key in ("name", "description", "labels", "body"):
            assert required_key in data, f"{stem} missing required key {required_key!r}"
        labels = data.get("labels")
        assert isinstance(labels, list) and labels, f"{stem} has no labels"
        for label in labels:
            assert label in KNOWN_LABELS, (
                f"{stem} references label {label!r} outside the fixed vocabulary "
                f"(docs/agents/triage-labels.md)"
            )


def test_each_category_has_a_template_with_a_category_label() -> None:
    """Both category roles (bug, enhancement) are covered by a template."""
    templates = _templates()
    label_sets = [set(t.get("labels", [])) for t in templates.values()]
    assert any("bug" in s for s in label_sets), "no template applies the bug category"
    assert any("enhancement" in s for s in label_sets), (
        "no template applies the enhancement category"
    )


def test_templates_apply_a_state_label() -> None:
    """Each template applies a needs-triage state role (the entry state for new issues)."""
    for stem, data in _templates().items():
        labels = set(data.get("labels", []))
        assert labels & STATE_LABELS, (
            f"{stem} does not apply a state role from {sorted(STATE_LABELS)}"
        )


def test_contributing_keeps_public_facing_boundaries() -> None:
    """CONTRIBUTING.md carries the HITL marker and the fixed boundaries.

    The "customer" term is allowed only in the glossary-definition context
    (Client = "legal customer"; "avoid customer"), mirroring the v0.9
    terminology-audit scoping (#232). Any NEW assertive use is caught.
    """
    text = CONTRIBUTING.read_text(encoding="utf-8")
    assert "<!-- HITL-REVIEW-REQUIRED" in text
    assert "educational only" in text.lower()
    assert "unaffiliated" in text.lower()
    assert "does not provide legal, compliance, audit" in text.lower()
    assert "reconstruct" in text.lower()
    for banned in ("we shipped", "publicly released", "is now published"):
        assert banned not in text.lower(), f"CONTRIBUTING uses banned phrase {banned!r}"
    for line in text.splitlines():
        if "customer" not in line.lower():
            continue
        joined = " ".join(line.lower().split())
        is_glossary_context = any(
            marker in joined
            for marker in ("client", "avoid", "never", "do not use", "legal customer")
        )
        assert is_glossary_context, (
            f"CONTRIBUTING uses 'customer' outside the glossary definition: {line.strip()!r}"
        )


def test_contributing_documents_fixed_ci_commands() -> None:
    """CONTRIBUTING points contributors at the fixed CI gate, not a redefinition."""
    text = CONTRIBUTING.read_text(encoding="utf-8")
    for command in ("uv sync --extra dev", "uv run ruff check .", "uv run pytest"):
        assert command in text, f"CONTRIBUTING missing fixed CI command {command!r}"
