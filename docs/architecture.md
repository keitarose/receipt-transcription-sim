# Architecture Guide

## Overview

The receipt transcription simulator models a consumer reward panel where members submit purchase receipts for transcription. The system processes receipts through a probabilistic pipeline that can fail, require correction, and ultimately approve or reject submissions.

## Module Dependency Graph

```
cli.py
  └── engine.py
        ├── population.py → models.py
        ├── retailers.py  → models.py
        ├── service.py    → models.py, retailers.py
        ├── incentives.py → models.py
        ├── events.py     → models.py
        ├── logger.py     → events.py, models.py
        └── config.py     → models.py
```

## Discrete-Event Engine

The engine (`engine.py`) uses a heap-based priority queue (Python's `heapq`) to process events in chronological order.

### Event Flow

```
PERIOD_TICK → update logger period
RECEIPT_ARRIVAL → process through service → schedule SERVICE_RESPONSE or RECEIPT_FAILED
SERVICE_RESPONSE → create RECEIPT_APPROVED or RECEIPT_REJECTED
RECEIPT_APPROVED → credit tokens to member
RECEIPT_REJECTED → logged only
```

### Scheduling

Each population member has an independent arrival process:

1. Compute effective rate = `λ_i × (1 + seg_mod + seasonal + engagement_boost) × baseline_engagement`
2. Apply tenure decay
3. Draw inter-arrival time from `Exponential(1/rate)`
4. Schedule next `RECEIPT_ARRIVAL` at `current_time + inter_arrival`

## Service Pipeline

```
Receipt arrives
    │
    ├─ compute_effective_p_fail(base, quality, retailer)
    │   p_fail = min(1, max(0, base × (1 - quality) × fail_modifier))
    │
    ├─ Bernoulli(p_fail) → Fail? → return None (RECEIPT_FAILED)
    │
    ├─ compute_effective_p_correct(base, quality, retailer)
    │   p_correct = min(1, max(0, base × (1 - quality) × correct_modifier))
    │
    ├─ Bernoulli(p_correct) → Corrected?
    │   ├─ Yes → response_time ~ N(μ_slow, σ_slow)
    │   └─ No  → response_time ~ N(μ_fast, σ_fast)
    │
    ├─ Bernoulli(base_p_approve) → Approved?
    │   ├─ Yes → tokens = base_reward
    │   └─ No  → tokens = 0
    │
    └─ Return ReceiptResponse
```

## Population Model

Members are characterised by:

- **Demographics**: age group, lifestage, social grade, geography, household size, pet ownership
- **Behaviour**: personal submission rate (Gamma), receipt quality (Beta), retailer mix (Dirichlet), baseline engagement (Beta)
- **Derived**: segmentation modifier (additive from demographics), tenure decay (linear)

## Incentive Feedback Loop

Token accumulation creates a mild positive feedback:

- `engagement_boost = min(0.3, token_balance × 0.001)`
- This boost is added to the effective submission rate, modestly increasing activity for rewarded members

## Configuration Merging

Scenario files are deep-merged onto the base config:

- Nested dicts are recursively merged
- Scalar values are overwritten
- The merged result is validated before constructing the `SimConfig` object

## Output Formats

- **Console**: Human-readable summary table
- **CSV**: One row per period with all metrics
- **JSON**: Structured output with `periods` array and `totals` object
- **Events CSV**: Raw event log with all event data fields
