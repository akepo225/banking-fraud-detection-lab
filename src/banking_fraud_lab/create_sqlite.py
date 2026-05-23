"""Command line entry point for creating the learner SQLite database."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from banking_fraud_lab.schema import LEARNER_FACING_TABLE_NAMES, TABLE_NAMES
from banking_fraud_lab.sqlite_loader import create_minimal_banking_world_sqlite


def main(argv: Sequence[str] | None = None) -> int:
    """
    Create the deterministic minimal banking world SQLite database from CLI arguments.
    
    Parameters:
        argv (Sequence[str] | None): Optional list of command-line arguments to parse; if None, uses the process arguments.
    
    Returns:
        int: Exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Create a SQLite database from the generated banking fraud lab tables."
    )
    parser.add_argument(
        "database_path",
        nargs="?",
        default="data/sample/minimal_world.sqlite",
        help="SQLite database file to create.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Generator seed.")
    parser.add_argument(
        "--include-protected",
        action="store_true",
        help="Include protected scenario answer keys in the SQLite database.",
    )
    args = parser.parse_args(argv)

    database_path = Path(args.database_path)
    connection = create_minimal_banking_world_sqlite(
        database_path,
        seed=args.seed,
        learner_facing=not args.include_protected,
    )
    connection.close()
    table_count = len(TABLE_NAMES if args.include_protected else LEARNER_FACING_TABLE_NAMES)
    print(f"Wrote {table_count} tables to {database_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
