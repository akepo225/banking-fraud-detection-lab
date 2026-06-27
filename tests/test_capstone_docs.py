"""Contract tests for the v0.9 capstone scenario briefs (issue #225).

The briefs frame the capstone analytic task from business context and must
respect the fixed glossary, the Detection pattern vocabulary, and the
pre-publication honesty boundary. These tests keep the briefs valid as later
slices link to them.
"""

from __future__ import annotations

import re
from pathlib import Path

from banking_fraud_lab.schema.detection_patterns import PATTERN_IDS

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


def _briefs() -> list[tuple[str, str, str]]:
    """Return (filename, institution, track-glossary-term) for each brief."""
    return [
        ("alpine_crest_brief.md", ALPINE_CREST, "Private-banking fraud detection"),
        ("novabank_brief.md", NOVABANK, "Digital-banking fraud detection"),
    ]


def test_capstone_briefs_exist() -> None:
    """One scenario brief per track lives under docs/capstone/."""
    assert CAPSTONE_DIR.is_dir()
    for filename, _, _ in _briefs():
        path = CAPSTONE_DIR / filename
        assert path.is_file(), f"missing capstone brief {filename}"


def test_capstone_briefs_use_hitl_marker_and_disclaimer() -> None:
    """Each brief carries the HITL marker and the educational-not-advice disclaimer."""
    for filename, _, _ in _briefs():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8")
        assert HITL_MARKER in text, f"{filename} missing HITL marker"
        assert "not legal" in text.lower(), f"{filename} missing not-advice disclaimer"
        assert "pre-publication" in text.lower(), f"{filename} missing beta framing"


def test_capstone_briefs_reference_valid_detection_patterns() -> None:
    """Every detection_patterns front-matter value must be a frozen pattern id."""
    front_matter_pattern = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
    for filename, _, _ in _briefs():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8")
        match = front_matter_pattern.search(text)
        assert match, f"{filename} missing YAML-style front matter"
        front_matter = match.group(1)
        patterns_line = next(
            line for line in front_matter.splitlines() if line.startswith("detection_patterns:")
        )
        pattern_ids = [
            token.strip()
            for token in patterns_line.split(":", 1)[1].split(",")
            if token.strip()
        ]
        assert pattern_ids, f"{filename} lists no detection patterns"
        for pattern_id in pattern_ids:
            assert pattern_id in PATTERN_IDS, (
                f"{filename} references unknown detection pattern {pattern_id!r}"
            )


def test_alpine_crest_brief_targets_private_banking_patterns() -> None:
    """The Alpine Crest brief targets the private-banking investigation patterns."""
    text = (CAPSTONE_DIR / "alpine_crest_brief.md").read_text(encoding="utf-8")
    for pattern_id in ("pb_high_value_movement", "circular_funds_movement"):
        assert pattern_id in text
    assert ALPINE_CREST in text
    assert "Banking relationship" in text


def test_novabank_brief_targets_digital_banking_patterns() -> None:
    """The NovaBank brief targets the digital-banking investigation patterns."""
    text = (CAPSTONE_DIR / "novabank_brief.md").read_text(encoding="utf-8")
    for pattern_id in ("digital_scam_to_mule", "new_beneficiary_payment", "mule_ring"):
        assert pattern_id in text
    assert NOVABANK in text
    assert "Client" in text and "User" in text


def test_capstone_briefs_avoid_banned_phrases() -> None:
    """Briefs must not use forbidden glossary/public-release language."""
    for filename, _, _ in _briefs():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8").lower()
        for phrase in BANNED_PHRASES:
            assert phrase not in text, f"{filename} contains banned phrase {phrase!r}"


def test_capstone_briefs_reference_dataset_command() -> None:
    """Each brief documents how to regenerate the deterministic capstone substrate."""
    for filename, _, _ in _briefs():
        text = (CAPSTONE_DIR / filename).read_text(encoding="utf-8")
        assert "banking_fraud_lab.capstone" in text, (
            f"{filename} does not document the capstone CLI"
        )
        assert "CAPSTONE_SEED" in text and "CAPSTONE_SCALE" in text
