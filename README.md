# vendor-risk-engine

**Transparent supplier-risk scoring across delivery, quality, commercial, compliance and dependency signals.**

[![Tests](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/vendor-risk-engine/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`vendor-risk-engine` converts measurable supplier-risk inputs into an explicit 0–100 score and LOW / MEDIUM / HIGH / CRITICAL classification.

The model supports procurement judgment rather than replacing it. Its compliance signal represents supplier-risk events; technical bid compliance remains an independent responsibility of [`bidlint`](https://github.com/yigitcan-ozturk/bidlint).

## Why vendor-risk-engine

Supplier risk is often buried inside subjective notes or blended into a final score without a clear explanation of what drove the result. `vendor-risk-engine` keeps delivery, quality, commercial exposure, compliance incidents and dependency risk visible as separate measurable components.

The objective is an inspectable, policy-aware risk signal that can be reviewed on its own and then passed into a broader supplier decision workflow.

## Decision boundary

`vendor-risk-engine` is responsible for **supplier operational and commercial risk scoring**.

It does:

- calculate explicit component risk scores;
- support configurable weights that must total 100%;
- support configurable LOW / MEDIUM / HIGH / CRITICAL thresholds;
- classify overall supplier risk;
- score individual suppliers or CSV batches;
- emit versioned structured JSON for downstream tools;
- provide a machine-readable result contract for integration.

It intentionally does **not**:

- determine technical bid compliance;
- compare quotation prices;
- interpret legal or regulatory compliance as legal advice;
- infer missing supplier facts;
- make final supplier approval decisions.

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

[`supplier-scorecard`](https://github.com/yigitcan-ozturk/supplier-scorecard) continues to read the top-level `vendor` and `score` fields directly, so the v0.4 structured additions remain backward compatible with the existing integration.

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

## Configurable risk thresholds

Default classification policy:

| Score | Risk |
| ---: | --- |
| 0–24.99 | LOW |
| 25–49.99 | MEDIUM |
| 50–74.99 | HIGH |
| 75–100 | CRITICAL |

The boundaries can be adjusted without changing the underlying supplier score:

```bash
vendor-risk-engine "Supplier A" \
  --on-time-delivery 85 \
  --defect-rate 3 \
  --prepayment-exposure 40 \
  --compliance-incidents 1 \
  --dependency-share 50 \
  --medium-threshold 20 \
  --high-threshold 40 \
  --critical-threshold 70
```

Thresholds must remain between 0 and 100 and satisfy:

```text
medium < high < critical
```

This separates **risk measurement** from **organizational risk appetite**: the numerical supplier score stays inspectable while classification policy can be configured for a procurement context.

## Risk model

| Component | Input | Default weight |
| --- | --- | ---: |
| Delivery | `100 - on-time delivery %` | 30% |
| Quality | `defect rate % × 10`, capped at 100 | 25% |
| Commercial | buyer prepayment exposure % | 20% |
| Compliance | incident-based supplier-risk scale | 15% |
| Dependency | category dependency share % | 10% |

## Versioned structured results

v0.4 adds explicit provenance and policy metadata while keeping the established top-level integration fields.

Example shape:

```json
{
  "vendor": "Supplier A",
  "score": 31.0,
  "risk": "MEDIUM",
  "meta": {
    "engine": "vendor-risk-engine",
    "engine_version": "0.4.0",
    "model_version": "vendor-risk-v1",
    "schema_version": "1.0"
  },
  "policy": {
    "weights": {},
    "thresholds": {}
  }
}
```

The complete machine-readable contract is available at [`schema/vendor-risk-result.schema.json`](schema/vendor-risk-result.schema.json).

This makes downstream decisions auditable: consumers can determine which engine release, model contract, weighting policy and classification thresholds produced a result.

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
- configurable weighting and threshold policy behavior;
- public package API and version metadata;
- wheel and source-distribution builds;
- package metadata with `twine check`;
- installation of the built wheel;
- the installed `vendor-risk-engine` console command and public package namespace.

## Engineering principles

- **Transparent components** — each risk contribution remains visible.
- **Configurable, not opaque** — weights and thresholds can change, but the active policy remains explicit and valid.
- **Versioned evidence** — structured results identify the engine, model and schema version that produced them.
- **No fabricated evidence** — missing supplier facts are not silently invented.
- **Separation of concerns** — supplier risk and technical compliance remain independent signals.
- **Review before authority** — the score informs procurement review; it does not approve a supplier.

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

- Historical supplier trend scoring
- Richer supplier compliance-risk models
- Pipeline portfolio mode with `supplier-scorecard`
- Policy profiles for category- or organization-specific risk appetite
- Stronger provenance for source datasets and review periods

## Status

Early-stage project, currently at **v0.4**. The current line provides transparent risk scoring, configurable weights and classification thresholds, batch ranking, CSV export, versioned structured results, an installable Python package and a console CLI.

## License

MIT License. See [`LICENSE`](LICENSE).
