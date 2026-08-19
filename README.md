# vendor-risk-engine

A lightweight Python CLI for scoring supplier/vendor risk using transparent operational, commercial, compliance and dependency signals.

[![Tests](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml)

## Why vendor-risk-engine

Supplier risk is usually spread across multiple signals: delivery performance, defects, payment exposure, compliance events and dependency on a single source. Reviewing those signals separately makes it difficult to compare vendors consistently.

`vendor-risk-engine` converts a small set of measurable supplier inputs into a transparent 0–100 risk score and a LOW / MEDIUM / HIGH / CRITICAL classification.

The model is intentionally simple and visible in the code. It is designed to support procurement judgment, not replace it.

## Features

- Score delivery risk from on-time delivery performance
- Score quality risk from supplier defect rate
- Include buyer prepayment exposure as commercial risk
- Include known compliance incidents
- Measure category dependency / concentration risk
- Produce a weighted 0–100 vendor risk score
- Assign LOW / MEDIUM / HIGH / CRITICAL risk levels
- Show the full score breakdown in the CLI output
- Run with Python only — no third-party runtime dependencies

## Quick start

### Requirements

- Python 3.11+

### Run

```bash
python main.py "Supplier A" \
  --on-time-delivery 85 \
  --defect-rate 3 \
  --prepayment-exposure 40 \
  --compliance-incidents 1 \
  --dependency-share 50
```

Example output:

```text
VENDOR RISK ENGINE v0.1
--------------------------------------------------
Vendor              : Supplier A
Overall risk score  : 31.00 / 100
Risk level          : MEDIUM

Risk breakdown
--------------------------------------------------
Delivery risk      :  15.00 / 100 x 30% =   4.50
Quality risk       :  30.00 / 100 x 25% =   7.50
Commercial risk    :  40.00 / 100 x 20% =   8.00
Compliance risk    :  40.00 / 100 x 15% =   6.00
Dependency risk    :  50.00 / 100 x 10% =   5.00
```

## Risk model

The v0.1 model uses five components:

| Component | Input | Weight |
| --- | --- | ---: |
| Delivery | `100 - on-time delivery %` | 30% |
| Quality | `defect rate % × 10`, capped at 100 | 25% |
| Commercial | buyer prepayment exposure % | 20% |
| Compliance | incident-based risk scale | 15% |
| Dependency | category dependency share % | 10% |

Compliance incidents are mapped as follows:

| Incidents | Risk score |
| ---: | ---: |
| 0 | 0 |
| 1 | 40 |
| 2 | 70 |
| 3+ | 100 |

Overall risk classification:

| Score | Risk |
| ---: | --- |
| 0–24.99 | LOW |
| 25–49.99 | MEDIUM |
| 50–74.99 | HIGH |
| 75–100 | CRITICAL |

The weights and thresholds are deliberately explicit so the scoring logic can be reviewed, challenged and changed as the project evolves.

## Tests

Run the test suite locally with:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same suite automatically on Python 3.11, 3.12 and 3.13.

## Related tools

This project is part of a small procurement-tooling set:

- [`rfqdiff`](https://github.com/yigitcan-ozturk/rfqdiff) — compare and score supplier quotations
- [`currency-normalizer`](https://github.com/yigitcan-ozturk/currency-normalizer) — normalize multi-currency supplier quotations
- [`payment-terms-parser`](https://github.com/yigitcan-ozturk/payment-terms-parser) — parse payment terms and buyer prepayment exposure

## Roadmap

- JSON output for system integration
- CSV batch scoring for vendor portfolios
- Configurable weights and thresholds
- Automatic input from `payment-terms-parser`
- Supplier trend scoring across review periods
- Integration with `rfqdiff`

## Status

Early-stage project, currently at **v0.1**. The first version provides a transparent, deterministic vendor-risk score from five procurement-relevant signals.

## License

MIT License. See [`LICENSE`](LICENSE).
