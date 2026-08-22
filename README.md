# vendor-risk-engine

**Transparent supplier-risk scoring across delivery, quality, commercial, compliance and dependency signals.**

[![Tests](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml)

`vendor-risk-engine` converts measurable supplier-risk inputs into an explicit 0–100 score and LOW / MEDIUM / HIGH / CRITICAL classification.

The model supports procurement judgment rather than replacing it. Its compliance signal represents supplier-risk events; technical bid compliance remains an independent responsibility of [`bidlint`](https://github.com/yigitcan-ozturk/bidlint).

## Install

Requirements: Python 3.11+.

```bash
git clone https://github.com/yigitcan-ozturk/vendor-risk-engine.git
cd vendor-risk-engine
python -m pip install .
```

The installed command is:

```bash
vendor-risk-engine --help
```

The original `python main.py ...` source-checkout workflow remains supported for backward compatibility.

## Quick start

```bash
vendor-risk-engine "Supplier A" \
  --on-time-delivery 85 \
  --defect-rate 3 \
  --prepayment-exposure 40 \
  --compliance-incidents 1 \
  --dependency-share 50
```

Structured output for the integrated scorecard:

```bash
vendor-risk-engine "Supplier A" \
  --on-time-delivery 85 \
  --defect-rate 3 \
  --prepayment-exposure 40 \
  --compliance-incidents 1 \
  --dependency-share 50 \
  --json > vendor-risk.json
```

`supplier-scorecard` reads the `vendor` and `score` fields directly from this JSON result.

## Public Python API

```python
import vendor_risk_engine

result = vendor_risk_engine.score_vendor(
    "Supplier A",
    on_time_delivery=90,
    defect_rate=1,
    prepayment_exposure=20,
    compliance_incidents=0,
    dependency_share=25,
)
```

## CSV batch scoring

```bash
vendor-risk-engine --csv samples/vendors.csv
vendor-risk-engine --csv samples/vendors.csv --json
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
vendor-risk-engine --csv samples/vendors.csv \
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

## Quality gates

GitHub Actions validates:

- unit tests on Python 3.11, 3.12 and 3.13;
- wheel and source-distribution builds;
- package metadata with `twine check`;
- installation of the built wheel;
- the installed `vendor-risk-engine` console command and public package namespace.

## Engineering procurement toolchain

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

Early-stage project, currently at **v0.3**. The current line provides transparent risk scoring, batch ranking, CSV export, an installable Python package and a console CLI.

## License

MIT License. See [`LICENSE`](LICENSE).
