"""Contract tests for the v0.9 capstone evaluation and communication artifacts (issue #229).

The rubric and presentation template carry the HITL marker, respect the fixed glossary, and
must grade / structure the real capstone deliverables (briefs, SQL feature extraction,
scoring notebooks, synthesis notebook). These tests keep the artifacts valid as later
slices link to them.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPSTONE_DIR = ROOT / "docs" / "capstone"
HITL_MARKER = "<!-- HITL-REVIEW-REQUIRED -->"

BANNED_PHRASES = (
    "customer",
    "publicly released",
    "is now published",
    "has been published",
    "reconstructs the",
    "reproduces the",
    "based on actual",
)

ALPINE_CREST = "Alpine Crest Private Bank"
NOVABANK = "NovaBank Digital"

RUBRIC = "rubric.md"
TEMPLATE = "presentation_template.md"


def _artifacts() -> list[str]:
    """Return the filenames of the capstone rubric and presentation template."""
    return [RUBRIC, TEMPLATE]


def test_capstone_rubric_and_template_exist() -> None:
    """The rubric and presentation template live under docs/capstone/."""
    assert CAPSTONE_DIR.is_dir()
    for filename in _artifacts():
        path = CAPSTONE_DIR / filename
        assert path.is_file(), f"missing capstone artifact {filename}"


def test_artifacts_carry_hitl_marker_and_disclaimer() -> None:
    """Each artifact carries the HITL marker and the educational-not-advice disclaimer."""
    for filename in _artifacts():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8")
        assert HITL_MARKER in text, f"{filename} missing HITL marker"
        assert "not legal" in text.lower(), f"{filename} missing not-advice disclaimer"
        assert "pre-publication" in text.lower(), f"{filename} missing beta framing"


def test_rubric_covers_all_six_dimensions() -> None:
    """The rubric covers every required dimension and rejects headline accuracy."""
    text = (CAPSTONE_DIR / RUBRIC).read_text(encoding="utf-8")
    for required in (
        "SQL quality",
        "Detection pattern",
        "Model evaluation",
        "Alert interpretation",
        "Alert lifecycle",
        "Governance",
        "Communication",
        "headline accuracy",
    ):
        assert required in text, f"rubric missing dimension/phrase {required!r}"


def test_rubric_traces_real_capstone_deliverables() -> None:
    """The rubric references only capstone deliverables that actually exist."""
    text = (CAPSTONE_DIR / RUBRIC).read_text(encoding="utf-8")
    for deliverable in (
        "alpine_crest_brief.md",
        "novabank_brief.md",
        "12_capstone_private_banking.sql",
        "13_capstone_digital_banking.sql",
        "alpine_crest_capstone_scoring.ipynb",
        "novabank_capstone_scoring.ipynb",
        "capstone_synthesis.ipynb",
    ):
        assert deliverable in text, f"rubric does not reference deliverable {deliverable!r}"


def test_artifacts_use_glossary_terms() -> None:
    """Both artifacts use the fixed glossary and name both fictional institutions."""
    for filename in _artifacts():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8")
        assert "Client" in text, f"{filename} missing glossary term Client"
        assert "User" in text, f"{filename} missing glossary term User"
        assert "Banking relationship" in text, f"{filename} missing glossary term Banking relationship"
        assert ALPINE_CREST in text, f"{filename} missing institution {ALPINE_CREST}"
        assert NOVABANK in text, f"{filename} missing institution {NOVABANK}"


def test_artifacts_avoid_banned_phrases() -> None:
    """Artifacts must not use forbidden glossary/public-release language."""
    for filename in _artifacts():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8").lower()
        for phrase in BANNED_PHRASES:
            assert phrase not in text, f"{filename} contains banned phrase {phrase!r}"
