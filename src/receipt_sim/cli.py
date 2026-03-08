"""Command-line interface for the receipt transcription simulation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from receipt_sim.config import load_config
from receipt_sim.engine import SimulationEngine


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="receipt-sim",
        description="Run a discrete-event simulation of a receipt transcription service.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).parent.parent.parent / "config" / "default.yaml"),
        help="Path to the base YAML configuration file.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Path to a scenario YAML overlay file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the random seed.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write summary CSV output.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        type=str,
        default=None,
        help="Path to write summary JSON output.",
    )
    parser.add_argument(
        "--events-csv",
        type=str,
        default=None,
        help="Path to write raw events CSV.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress console summary output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    args = parse_args(argv)

    config = load_config(args.config, args.scenario)

    if args.seed is not None:
        from dataclasses import replace

        new_sim = replace(config.simulation, seed=args.seed)
        config = replace(config, simulation=new_sim)

    engine = SimulationEngine(config)
    logger = engine.run()

    summary_df = logger.to_dataframe()

    if not args.quiet:
        _print_summary(logger)

    if args.output:
        summary_df.to_csv(args.output, index=False)

    if args.json_output:
        _write_json(logger, args.json_output)

    if args.events_csv:
        events_df = logger.events_to_dataframe()
        events_df.to_csv(args.events_csv, index=False)

    return 0


def _print_summary(logger) -> None:
    """Print a human-readable summary to stdout."""
    summaries = logger.get_period_summaries()
    totals = logger.get_totals()

    print("=" * 50)
    print("Receipt Transcription Simulation — Summary")
    print("=" * 50)
    print(f"Periods simulated:  {len(summaries)}")
    print(f"Total events:       {totals['events']}")
    print(f"Total arrivals:     {totals['arrivals']}")
    print(f"Total failures:     {totals['failures']}")
    print(f"Total approvals:    {totals['approvals']}")
    print(f"Total rejections:   {totals['rejections']}")
    print(f"Total tokens:       {totals['tokens']}")

    if totals["arrivals"] > 0:
        print(f"Failure rate:       {totals['failures'] / totals['arrivals']:.2%}")
    if totals["approvals"] + totals["rejections"] > 0:
        print(
            f"Approval rate:      "
            f"{totals['approvals'] / (totals['approvals'] + totals['rejections']):.2%}"
        )
    print("=" * 50)


def _write_json(logger, path: str) -> None:
    """Write summary data as JSON."""
    summaries = logger.get_period_summaries()
    data = {
        "periods": [
            {
                "period": s.period,
                "arrivals": s.arrivals,
                "failures": s.failures,
                "responses": s.responses,
                "approvals": s.approvals,
                "rejections": s.rejections,
                "corrections": s.corrections,
                "total_tokens": s.total_tokens,
                "failure_rate": round(s.failure_rate, 6),
                "approval_rate": round(s.approval_rate, 6),
                "correction_rate": round(s.correction_rate, 6),
                "mean_response_time": round(s.mean_response_time, 6),
            }
            for s in summaries
        ],
        "totals": logger.get_totals(),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
