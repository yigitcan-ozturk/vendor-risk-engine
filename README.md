# vendor-risk-engine

A lightweight Python CLI for scoring supplier/vendor risk using transparent operational, commercial, compliance and dependency signals.

[![Tests](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml)

## Why vendor-risk-engine

Supplier risk is usually spread across multiple signals: delivery performance, defects, payment exposure, compliance events and dependency on a single source. `vendor-risk-engine` converts those measurable inputs into a transparent 0–100 risk score and a LOW / MEDIUM / HIGH / CRITICAL classification.

The model is intended to support procurement judgment, not replace it. Its compliance signal represents supplier-risk events; technical bid compliance remains an independent responsibility of [`bidlint`](https://github.com/yigitcan-ozturk/bidlint).

## Features

- Score delivery risk from on-time delivery performance
- Score quality risk from supplier defect rate
- Include buyer prepayment exposure as commercial risk
- Include known compliance incidents
- Measure category dependency / concentration risk
- Produce a weighted 0–100 vendor risk score
- Assign LOW / MEDIUM / HIGH / CRITICAL risk levels
- Return structured JSON for system integration
- Score multiple vendors from CSV
- Rank portfolio results
- Override risk-component weights
- Export ranked results to CSV
- Run with Python only — no third-party runtime dependencies

## Quick start

```bash
python main.py "Supplier A" \
  --on-time-delivery 85 \
  --defect-rate 3 \
  --prepayment-exposure 40 \
  --compliance-incidents 1 \
  --dependency-share 50
```

Structured output for the integrated scorecard:

```bash
python main.py "Supplier A" \
  --on-time-delivery 85 \
  --defect-rate 3 \
  --prepayment-exposure 40 \
  --compliance-incidents 1 \
  --dependency-share 50 \
  --json > vendor-risk.json
```

`supplier-scorecard` reads the `vendor` and `score` fields directly from this JSON result.

## CSV batch scoring

```bash
python main.py --csv samples/vendors.csv
```

Batch JSON is also supported:

```bash
python main.py --csv samples/vendors.csv --json
```

`supplier-scorecard` can select a matching supplier from either a single vendor-risk object or a batch JSON list.

## Configurable weights

Defaults:

| Component | Default weight |
| --- | ---: |
| Delivery | 30% |
| Quality | 25% |
| Commercial | 20% |
| Compliance | 15% |
| Dependency | 10% |

Example override:

```bash
python main.py --csv samples/vendors.csv \
  --delivery-weight 40 \
  --quality-weight 30 \
  --commercial-weight 15 \
  --compliance-weight 10 \
  --dependency-weight 5
```

Weights must be non-negative and total exactly 100%.

## Risk model

| Component | Input | Default weight |
| --- | --- | ---: |
| Delivery | `100 - on-time delivery %` | 30% |
| Quality | `defect rate % × 10`, capped at 100 | 25% |
| Commercial | buyer prepayment exposure % | 20% |
| Compliance | incident-based supplier-risk scale | 15% |
| Dependency | category dependency share % | 10% |

Overall risk classification:

| Score | Risk |
| ---: | --- |
| 0–24.99 | LOW |
| 25–49.99 | MEDIUM |
| 50–74.99 | HIGH |
| 75–100 | CRITICAL |

## Pipeline role

```text
currency-normalizer ──> rfqdiff ───────────────────────┐
                                                        │
payment-terms-parser ──────────────────────────────────┼──> supplier-scorecard
                                                        │
vendor-risk-engine ────────────────────────────────────┤
                                                        │
bidlint ──> technical compliance ──────────────────────┘
```

`vendor-risk-engine` contributes the supplier-risk signal to `supplier-scorecard`; `bidlint` contributes technical compliance separately. This separation keeps operational/vendor risk and engineering compliance independently inspectable.

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the suite automatically on Python 3.11, 3.12 and 3.13.

## Procurement tooling suite

| Tool | Role |
| --- | --- |
| [`currency-normalizer`](https://github.com/yigitcan-ozturk/currency-normalizer) | Normalize quotation values across currencies |
| [`rfqdiff`](https://github.com/yigitcan-ozturk/rfqdiff) | Compare and score normalized quotations |
| [`payment-terms-parser`](https://github.com/yigitcan-ozturk/payment-terms-parser) | Convert payment terms into commercial-risk signals |
| **[`vendor-risk-engine`](https://github.com/yigitcan-ozturk/vendor-risk-engine)** | Score operational, quality, supplier-compliance and dependency risk |
| [`bidlint`](https://github.com/yigitcan-ozturk/bidlint) | Produce evidence-backed technical-compliance findings and scores |
| [`supplier-scorecard`](https://github.com/yigitcan-ozturk/supplier-scorecard) | Combine commercial, risk and technical signals into one supplier recommendation |

## Roadmap

- Configurable risk thresholds
- Historical supplier trend scoring
- Richer supplier compliance-risk models
- Pipeline portfolio mode with `supplier-scorecard`
- More explicit source/version metadata in structured results

## Status

Early-stage project, currently at **v0.3**. The current version provides configurable transparent risk scoring, batch ranking and CSV export, and its JSON output is now consumed directly by `supplier-scorecard`.

## License

MIT License. See [`LICENSE`](LICENSE).
