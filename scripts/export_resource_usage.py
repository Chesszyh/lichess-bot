#!/usr/bin/env python3
"""Export lichess-bot resource usage summaries."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.resource_monitor import read_resource_samples, summarize_resource_samples, write_summary_csv


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Export lichess-bot resource usage by game, day, or week.")
    parser.add_argument("--input", default="resource_records",
                        help="CSV file or directory containing resource_usage.csv. Default: resource_records")
    parser.add_argument("--group", choices=["game", "day", "week"], default="day",
                        help="Summary grouping. Default: day")
    parser.add_argument("--output", help="Output CSV path. Defaults to stdout.")
    return parser.parse_args()


def main() -> None:
    """Export resource usage summary."""
    args = parse_args()
    samples = read_resource_samples(Path(args.input))
    rows = summarize_resource_samples(samples, args.group)
    write_summary_csv(rows, Path(args.output) if args.output else None)


if __name__ == "__main__":
    main()
