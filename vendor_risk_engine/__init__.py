"""Public Python API for vendor-risk-engine."""

from main import (
    DEFAULT_WEIGHTS,
    RISK_COMPONENTS,
    VERSION,
    compliance_risk,
    rank_results,
    risk_level,
    score_csv,
    score_vendor,
    validate_weights,
)

__version__ = "0.3.0"

__all__ = [
    "DEFAULT_WEIGHTS",
    "RISK_COMPONENTS",
    "VERSION",
    "__version__",
    "compliance_risk",
    "rank_results",
    "risk_level",
    "score_csv",
    "score_vendor",
    "validate_weights",
]
