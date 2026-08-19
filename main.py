import argparse


WEIGHTS = {
    "delivery": 0.30,
    "quality": 0.25,
    "commercial": 0.20,
    "compliance": 0.15,
    "dependency": 0.10,
}


def validate_percent(name, value):
    if value < 0 or value > 100:
        raise ValueError(f"{name} must be between 0 and 100.")


def compliance_risk(incidents):
    if incidents < 0:
        raise ValueError("compliance incidents cannot be negative.")

    if incidents == 0:
        return 0.0
    if incidents == 1:
        return 40.0
    if incidents == 2:
        return 70.0

    return 100.0


def risk_level(score):
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"

    return "LOW"


def score_vendor(
    vendor,
    on_time_delivery,
    defect_rate,
    prepayment_exposure,
    compliance_incidents,
    dependency_share,
):
    validate_percent("on-time delivery", on_time_delivery)
    validate_percent("defect rate", defect_rate)
    validate_percent("prepayment exposure", prepayment_exposure)
    validate_percent("dependency share", dependency_share)

    delivery = 100.0 - on_time_delivery
    quality = min(defect_rate * 10.0, 100.0)
    commercial = prepayment_exposure
    compliance = compliance_risk(compliance_incidents)
    dependency = dependency_share

    component_scores = {
        "delivery": delivery,
        "quality": quality,
        "commercial": commercial,
        "compliance": compliance,
        "dependency": dependency,
    }

    weighted_scores = {
        name: component_scores[name] * WEIGHTS[name]
        for name in WEIGHTS
    }

    total = round(sum(weighted_scores.values()), 2)

    return {
        "vendor": vendor,
        "score": total,
        "risk": risk_level(total),
        "components": component_scores,
        "weighted": weighted_scores,
        "inputs": {
            "on_time_delivery": on_time_delivery,
            "defect_rate": defect_rate,
            "prepayment_exposure": prepayment_exposure,
            "compliance_incidents": compliance_incidents,
            "dependency_share": dependency_share,
        },
    }


def print_report(result):
    print()
    print("VENDOR RISK ENGINE v0.1")
    print("-" * 50)
    print(f"Vendor              : {result['vendor']}")
    print(f"Overall risk score  : {result['score']:.2f} / 100")
    print(f"Risk level          : {result['risk']}")
    print()
    print("Risk breakdown")
    print("-" * 50)

    labels = {
        "delivery": "Delivery risk",
        "quality": "Quality risk",
        "commercial": "Commercial risk",
        "compliance": "Compliance risk",
        "dependency": "Dependency risk",
    }

    for name in WEIGHTS:
        component = result["components"][name]
        weighted = result["weighted"][name]
        weight_percent = int(WEIGHTS[name] * 100)
        print(
            f"{labels[name]:19}: {component:6.2f} / 100 "
            f"x {weight_percent:>2}% = {weighted:6.2f}"
        )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Score supplier/vendor risk using transparent operational, "
            "commercial, compliance and dependency signals."
        )
    )

    parser.add_argument("vendor", help="Vendor or supplier name.")
    parser.add_argument(
        "--on-time-delivery",
        type=float,
        required=True,
        help="On-time delivery performance as a percentage (0-100).",
    )
    parser.add_argument(
        "--defect-rate",
        type=float,
        required=True,
        help="Defect rate as a percentage (0-100).",
    )
    parser.add_argument(
        "--prepayment-exposure",
        type=float,
        required=True,
        help="Buyer payment exposure before delivery as a percentage (0-100).",
    )
    parser.add_argument(
        "--compliance-incidents",
        type=int,
        required=True,
        help="Known compliance incidents in the review period.",
    )
    parser.add_argument(
        "--dependency-share",
        type=float,
        required=True,
        help="Share of category dependency concentrated on this vendor (0-100).",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = score_vendor(
            vendor=args.vendor,
            on_time_delivery=args.on_time_delivery,
            defect_rate=args.defect_rate,
            prepayment_exposure=args.prepayment_exposure,
            compliance_incidents=args.compliance_incidents,
            dependency_share=args.dependency_share,
        )
    except ValueError as exc:
        parser.error(str(exc))

    print_report(result)


if __name__ == "__main__":
    main()
