# Receipt Transcription Simulation

A discrete-event simulation of a receipt transcription service, modelling user populations, receipt submission behaviour, transcription processing, and token incentive mechanics.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ (for the dashboard)

### Installation

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies (optional)
cd frontend && npm install && cd ..
```

### Run the Simulation

```bash
# Basic run with console summary
uv run receipt-sim

# Custom seed
uv run receipt-sim --seed 123

# Export results
uv run receipt-sim --json output.json --output summary.csv --quiet

# Run with a scenario overlay
uv run receipt-sim --scenario config/scenarios/high_failure.yaml --json output.json

# Export raw events
uv run receipt-sim --events-csv events.csv --quiet
```

### View in Dashboard

```bash
# 1. Generate JSON output
uv run receipt-sim --json output.json --quiet

# 2. Start the dashboard
cd frontend && npm run dev

# 3. Open http://localhost:3000 and upload output.json
```

## Project Structure

```
receipt-transcription-sim/
├── config/
│   ├── default.yaml              # Base configuration
│   └── scenarios/
│       ├── baseline.yaml          # Baseline scenario (seed=42)
│       └── high_failure.yaml      # High failure rate scenario
├── src/receipt_sim/
│   ├── __init__.py
│   ├── models.py                  # Data models (frozen dataclasses)
│   ├── config.py                  # YAML loading, merging, validation
│   ├── retailers.py               # Retailer types and profiles
│   ├── events.py                  # Event types and factory functions
│   ├── population.py              # Population generation
│   ├── service.py                 # Transcription service logic
│   ├── incentives.py              # Token rewards and engagement
│   ├── logger.py                  # Event logging and period summaries
│   ├── engine.py                  # Discrete-event simulation engine
│   └── cli.py                     # Command-line interface
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_retailers.py
│   ├── test_events.py
│   ├── test_population.py
│   ├── test_service.py
│   ├── test_incentives.py
│   ├── test_logger.py
│   ├── test_engine.py
│   ├── test_cli.py
│   └── test_integration.py
├── frontend/                      # React + Recharts dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── components/
│   │       ├── Dashboard.jsx
│   │       ├── FileUpload.jsx
│   │       ├── SummaryCards.jsx
│   │       └── charts/
│   │           ├── ArrivalsChart.jsx
│   │           ├── FailureRateChart.jsx
│   │           ├── ApprovalRateChart.jsx
│   │           ├── ResponseTimeChart.jsx
│   │           ├── TokensChart.jsx
│   │           └── CorrectionRateChart.jsx
│   ├── package.json
│   └── vite.config.js
├── docs/
│   └── architecture.md
├── pyproject.toml
└── README.md
```

## Architecture

### Simulation Pipeline

1. **Population Generation** — Draw demographic attributes, submission rates, quality scores, and retailer preferences from configured distributions
2. **Event Scheduling** — Each member's next receipt arrival is scheduled via exponential inter-arrival times, modulated by seasonality, engagement, and tenure decay
3. **Receipt Processing** — The transcription service applies failure, correction, response time, and approval logic
4. **Incentive Engine** — Approved receipts award tokens, which feed back into engagement boosts
5. **Logging** — All events are collected and aggregated into per-period summaries

### Key Design Decisions

- **Immutable models**: All configuration and request/response types use frozen dataclasses
- **Stateless service**: `process_receipt()` is a pure function — all state lives in the engine
- **Heapq event queue**: Standard library priority queue for O(log n) event scheduling
- **Numpy RNG**: `np.random.Generator` with explicit seeding for full reproducibility

## Configuration

The simulation is configured via YAML files. See [config/default.yaml](config/default.yaml) for all available parameters.

### Key Parameters

| Section      | Parameter              | Description                      |
| ------------ | ---------------------- | -------------------------------- |
| `simulation` | `seed`                 | Random seed for reproducibility  |
| `simulation` | `duration`             | Total simulation time in hours   |
| `simulation` | `period_length`        | Period tick interval (hours)     |
| `service`    | `base_p_fail`          | Base receipt failure probability |
| `service`    | `base_p_correct`       | Base correction probability      |
| `service`    | `base_p_approve`       | Base approval probability        |
| `service`    | `base_reward`          | Tokens per approved receipt      |
| `population` | `size`                 | Number of panel members          |
| `activity`   | `seasonal_multipliers` | Monthly rate modifiers           |

### Scenarios

Create scenario files to override specific parameters:

```yaml
# config/scenarios/my_scenario.yaml
service:
  base_p_fail: 0.15
simulation:
  seed: 99
```

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=receipt_sim --cov-report=term-missing

# Specific module
uv run pytest tests/test_engine.py -v
```

## CLI Reference

```
usage: receipt-sim [-h] [--config CONFIG] [--scenario SCENARIO] [--seed SEED]
                   [--output OUTPUT] [--json JSON] [--events-csv EVENTS_CSV]
                   [--quiet]

options:
  --config CONFIG       Path to the base YAML configuration file
  --scenario SCENARIO   Path to a scenario YAML overlay file
  --seed SEED           Override the random seed
  --output OUTPUT       Path to write summary CSV output
  --json JSON           Path to write summary JSON output
  --events-csv CSV      Path to write raw events CSV
  --quiet               Suppress console summary output
```

## License

MIT
