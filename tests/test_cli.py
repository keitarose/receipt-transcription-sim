"""Tests for the CLI module."""

import json
import os
import tempfile
from pathlib import Path

from receipt_sim.cli import main, parse_args

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")
SCENARIO_PATH = str(
    Path(__file__).parent.parent / "config" / "scenarios" / "baseline.yaml"
)


class TestParseArgs:
    def test_defaults(self):
        """TC-CLI-01: Default arguments are set."""
        args = parse_args([])
        assert args.scenario is None
        assert args.seed is None
        assert args.output is None
        assert args.json_output is None
        assert args.quiet is False

    def test_all_flags(self):
        """TC-CLI-02: All flags are parsed."""
        args = parse_args(
            [
                "--config",
                "c.yaml",
                "--scenario",
                "s.yaml",
                "--seed",
                "99",
                "--output",
                "out.csv",
                "--json",
                "out.json",
                "--events-csv",
                "ev.csv",
                "--quiet",
            ]
        )
        assert args.config == "c.yaml"
        assert args.scenario == "s.yaml"
        assert args.seed == 99
        assert args.output == "out.csv"
        assert args.json_output == "out.json"
        assert args.events_csv == "ev.csv"
        assert args.quiet is True


class TestMainExecution:
    def test_run_quiet(self):
        """TC-CLI-03: Quiet run completes and returns 0."""
        result = main(["--config", CONFIG_PATH, "--quiet", "--seed", "42"])
        assert result == 0

    def test_run_with_scenario(self):
        """TC-CLI-04: Run with scenario overlay."""
        result = main(
            [
                "--config",
                CONFIG_PATH,
                "--scenario",
                SCENARIO_PATH,
                "--quiet",
            ]
        )
        assert result == 0

    def test_csv_output(self):
        """TC-CLI-05: CSV output is written."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            out_path = f.name
        try:
            result = main(
                [
                    "--config",
                    CONFIG_PATH,
                    "--seed",
                    "42",
                    "--output",
                    out_path,
                    "--quiet",
                ]
            )
            assert result == 0
            assert os.path.exists(out_path)
            content = Path(out_path).read_text()
            assert "arrivals" in content
            assert "failure_rate" in content
        finally:
            os.unlink(out_path)

    def test_json_output(self):
        """TC-CLI-06: JSON output is written and valid."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        try:
            result = main(
                [
                    "--config",
                    CONFIG_PATH,
                    "--seed",
                    "42",
                    "--json",
                    out_path,
                    "--quiet",
                ]
            )
            assert result == 0
            with open(out_path) as f:
                data = json.load(f)
            assert "periods" in data
            assert "totals" in data
            assert data["totals"]["events"] > 0
        finally:
            os.unlink(out_path)

    def test_events_csv_output(self):
        """TC-CLI-07: Events CSV output is written."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            out_path = f.name
        try:
            result = main(
                [
                    "--config",
                    CONFIG_PATH,
                    "--seed",
                    "42",
                    "--events-csv",
                    out_path,
                    "--quiet",
                ]
            )
            assert result == 0
            content = Path(out_path).read_text()
            assert "event_type" in content
        finally:
            os.unlink(out_path)

    def test_seed_override(self):
        """TC-CLI-08: Seed override produces deterministic output."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            p1 = f.name
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            p2 = f.name
        try:
            main(["--config", CONFIG_PATH, "--seed", "77", "--json", p1, "--quiet"])
            main(["--config", CONFIG_PATH, "--seed", "77", "--json", p2, "--quiet"])
            d1 = json.loads(Path(p1).read_text())
            d2 = json.loads(Path(p2).read_text())
            assert d1["totals"] == d2["totals"]
        finally:
            os.unlink(p1)
            os.unlink(p2)
