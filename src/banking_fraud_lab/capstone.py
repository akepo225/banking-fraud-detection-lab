"""Deterministic capstone datasets for the v0.9 integration capstone.

The capstone is an *integration* surface, not a new feature family: it reuses
the existing scenario-injection generators and the learner-facing /
protected-answer-key separation so every later capstone slice (SQL features,
scoring notebooks, synthesis, governance) builds on one shared seed.

This module fixes a deterministic capstone configuration (seed + scale +
scenario prevalence) for each **Fraud detection track** and exposes both the
grading export (full tables WITH protected answer keys) and the learner-facing
export (tables WITHOUT protected answer keys). No new tables or columns are
introduced (ADR-0002 additive schema); the underlying
``inject_private_banking_transaction_fraud`` and
``inject_digital_fraud_scenarios`` generators are reused unchanged.

Alpine Crest Private Bank capstone:

- Substrate: ``generate_minimal_banking_world`` + private-banking transaction
  fraud injection (Detection pattern ``pb_transaction_fraud``, with
  ``pb_high_value_movement`` false-positive context).
- Graph investigation target: ``circular_funds_movement`` (graph-derived from
  the same transactions; mined by the graph layer in the synthesis slice).

NovaBank Digital capstone:

- Substrate: ``generate_minimal_banking_world`` + the full v0.4 digital
  scenario mix (Detection patterns ``digital_scam_to_mule``,
  ``new_beneficiary_payment``, ``session_payment_velocity``).
- Graph investigation target: ``mule_ring`` (graph-derived from the same
  transactions; mined by the graph layer in the synthesis slice).
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from banking_fraud_lab.generators import (
    DEFAULT_SCALE_PROFILE,
    DatasetScaleProfile,
    build_learner_facing_views,
    generate_minimal_banking_world,
)
from banking_fraud_lab.generators.digital_banking import inject_digital_fraud_scenarios
from banking_fraud_lab.generators.private_banking import (
    inject_private_banking_transaction_fraud,
)
from banking_fraud_lab.schema import TABLE_NAMES

CAPSTONE_SEED = 42
CAPSTONE_SCALE = DEFAULT_SCALE_PROFILE

PRIVATE_BANKING_TRACK = "private_banking"
DIGITAL_BANKING_TRACK = "digital_banking"
CAPSTONE_TRACKS: tuple[str, ...] = (PRIVATE_BANKING_TRACK, DIGITAL_BANKING_TRACK)

PRIVATE_BANKING_SCENARIO_PREVALENCE = 0.2
DIGITAL_BANKING_SCENARIO_PREVALENCE = 0.5
DIGITAL_BANKING_NOISY_OUTCOME_RATE = 0.3


def generate_capstone_private_banking_world(
    seed: int = CAPSTONE_SEED,
    output_dir: Path | None = None,
    *,
    scale: str | DatasetScaleProfile = CAPSTONE_SCALE,
    scenario_prevalence: float = PRIVATE_BANKING_SCENARIO_PREVALENCE,
) -> dict[str, pd.DataFrame]:
    """Generate the Alpine Crest capstone grading tables with protected answer keys.

    Reuses ``generate_minimal_banking_world`` and
    ``inject_private_banking_transaction_fraud`` so the capstone carries the
    same Partner, Banking relationship, Client, Alert lifecycle, and
    Detection pattern lineage as the rest of the private-banking track. The
    returned tables include ``protected_scenario_answer_keys`` for grading.

    Args:
        seed: Deterministic generation seed (defaults to the capstone seed).
        output_dir: Optional directory to write generated CSV tables.
        scale: Named scale profile or a ``DatasetScaleProfile``.
        scenario_prevalence: Bounded proportion of private-banking transactions
            that receive the transaction-fraud scenario label.

    Returns:
        Grading tables with all generated entities, including protected answer
        keys.
    """
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
    scenario_tables = inject_private_banking_transaction_fraud(
        tables,
        scenario_prevalence=scenario_prevalence,
    )

    if output_dir is not None:
        _write_tables(scenario_tables, output_dir)

    return scenario_tables


def generate_learner_facing_capstone_private_banking_world(
    seed: int = CAPSTONE_SEED,
    output_dir: Path | None = None,
    *,
    scale: str | DatasetScaleProfile = CAPSTONE_SCALE,
    scenario_prevalence: float = PRIVATE_BANKING_SCENARIO_PREVALENCE,
) -> dict[str, pd.DataFrame]:
    """Generate learner-facing Alpine Crest capstone tables without protected keys.

    Wraps :func:`generate_capstone_private_banking_world` and applies
    :func:`build_learner_facing_views` so the ``protected_scenario_answer_keys``
    table is removed from learner-facing exports.
    """
    tables = generate_capstone_private_banking_world(
        seed=seed,
        scale=scale,
        scenario_prevalence=scenario_prevalence,
    )
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        _write_tables(learner_tables, output_dir)

    return learner_tables


def generate_capstone_digital_banking_world(
    seed: int = CAPSTONE_SEED,
    output_dir: Path | None = None,
    *,
    scale: str | DatasetScaleProfile = CAPSTONE_SCALE,
    scenario_prevalence: float = DIGITAL_BANKING_SCENARIO_PREVALENCE,
    noisy_outcome_rate: float = DIGITAL_BANKING_NOISY_OUTCOME_RATE,
) -> dict[str, pd.DataFrame]:
    """Generate the NovaBank Digital capstone grading tables with protected answer keys.

    Reuses ``generate_minimal_banking_world`` and
    ``inject_digital_fraud_scenarios`` (the full v0.4 mix of scam-to-mule,
    account-takeover, onboarding-abuse, and beneficiary-change injections) so
    the capstone carries the same Client / User / Partner separation, session
    telemetry, and Detection pattern lineage as the rest of the digital-banking
    track. The returned tables include ``protected_scenario_answer_keys`` for
    grading.

    Args:
        seed: Deterministic generation seed (defaults to the capstone seed).
        output_dir: Optional directory to write generated CSV tables.
        scale: Named scale profile or a ``DatasetScaleProfile``.
        scenario_prevalence: Bounded proportion of NovaBank Digital accounts
            that participate in each scenario family.
        noisy_outcome_rate: Bounded proportion of v0.4 scenario cases whose
            triage outcome deliberately disagrees with the true protected
            label.

    Returns:
        Grading tables with all generated entities, including protected answer
        keys.
    """
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
    scenario_tables = inject_digital_fraud_scenarios(
        tables,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
    )

    if output_dir is not None:
        _write_tables(scenario_tables, output_dir)

    return scenario_tables


def generate_learner_facing_capstone_digital_banking_world(
    seed: int = CAPSTONE_SEED,
    output_dir: Path | None = None,
    *,
    scale: str | DatasetScaleProfile = CAPSTONE_SCALE,
    scenario_prevalence: float = DIGITAL_BANKING_SCENARIO_PREVALENCE,
    noisy_outcome_rate: float = DIGITAL_BANKING_NOISY_OUTCOME_RATE,
) -> dict[str, pd.DataFrame]:
    """Generate learner-facing NovaBank Digital capstone tables without protected keys.

    Wraps :func:`generate_capstone_digital_banking_world` and applies
    :func:`build_learner_facing_views` so the ``protected_scenario_answer_keys``
    table is removed from learner-facing exports.
    """
    tables = generate_capstone_digital_banking_world(
        seed=seed,
        scale=scale,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
    )
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        _write_tables(learner_tables, output_dir)

    return learner_tables


def main(argv: Sequence[str] | None = None) -> int:
    """Generate capstone dataset CSVs for one or both tracks from the CLI.

    Reproduces the deterministic capstone dataset(s) so a learner (or capstone
    notebook) can regenerate the substrate without hidden maintainer state.
    Defaults to the fixed capstone seed and scale.
    """
    parser = argparse.ArgumentParser(
        description="Generate deterministic v0.9 capstone datasets for both tracks.",
    )
    parser.add_argument(
        "--track",
        choices=CAPSTONE_TRACKS + ("both",),
        default="both",
        help="Capstone track to generate.",
    )
    parser.add_argument(
        "--learner-facing",
        action="store_true",
        help="Exclude protected answer keys (learner-facing export).",
    )
    parser.add_argument("--seed", type=int, default=CAPSTONE_SEED, help="Generator seed.")
    parser.add_argument("--scale", default=CAPSTONE_SCALE, help="Named generator scale profile.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for CSV files (defaults to a per-track directory).",
    )
    args = parser.parse_args(argv)

    tracks = CAPSTONE_TRACKS if args.track == "both" else (args.track,)
    wrote_any = False
    for track in tracks:
        if args.output is not None:
            output_dir = args.output / track
        else:
            output_dir = Path(f"data/capstone/{track}")
        tables = _generate_track(
            track,
            seed=args.seed,
            scale=args.scale,
            learner_facing=args.learner_facing,
        )
        _write_tables(tables, output_dir)
        print(f"Wrote {len(tables)} tables for {track} capstone to {output_dir}")
        wrote_any = True

    return 0 if wrote_any else 1


def _generate_track(
    track: str,
    *,
    seed: int,
    scale: str | DatasetScaleProfile,
    learner_facing: bool,
) -> dict[str, pd.DataFrame]:
    """Dispatch to the matching capstone track generator."""
    if track == PRIVATE_BANKING_TRACK:
        if learner_facing:
            return generate_learner_facing_capstone_private_banking_world(seed=seed, scale=scale)
        return generate_capstone_private_banking_world(seed=seed, scale=scale)
    if track == DIGITAL_BANKING_TRACK:
        if learner_facing:
            return generate_learner_facing_capstone_digital_banking_world(seed=seed, scale=scale)
        return generate_capstone_digital_banking_world(seed=seed, scale=scale)
    raise ValueError(f"Unknown capstone track {track!r}; expected one of: {CAPSTONE_TRACKS}")


def _write_tables(tables: Mapping[str, pd.DataFrame], output_dir: Path) -> None:
    """Write generated tables in schema order to CSV files with LF line endings.

    Mirrors the byte-identity convention used by the minimal-world and scenario
    generators (pinned UTF-8 + LF) so regenerated capstone datasets stay
    cross-platform deterministic.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for table_name in TABLE_NAMES:
        if table_name in tables:
            tables[table_name].to_csv(
                output_path / f"{table_name}.csv",
                index=False,
                encoding="utf-8",
                lineterminator="\n",
            )


__all__ = [
    "CAPSTONE_SCALE",
    "CAPSTONE_SEED",
    "CAPSTONE_TRACKS",
    "DIGITAL_BANKING_NOISY_OUTCOME_RATE",
    "DIGITAL_BANKING_SCENARIO_PREVALENCE",
    "DIGITAL_BANKING_TRACK",
    "PRIVATE_BANKING_SCENARIO_PREVALENCE",
    "PRIVATE_BANKING_TRACK",
    "generate_capstone_digital_banking_world",
    "generate_capstone_private_banking_world",
    "generate_learner_facing_capstone_digital_banking_world",
    "generate_learner_facing_capstone_private_banking_world",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
