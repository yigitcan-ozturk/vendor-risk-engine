import argparse
import csv
import json


VERSION = "0.2"

WEIGHTS = {
    "delivery": 0.30,
    "quality": 0.25,
    "commercial": 0.20,
    "compliance": 0.15,
    "dependency": 0.10,
}

CSV_COLUMNS = (
    "vendor",
    "on_time_delivery",
    "defect_rate",
    "prepayment_exposure",
    "compliance_incidents",
    "dependency_share",
)


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
    if not str(vendor).strip():
        raise ValueError("vendor name cannot be empty.")

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
        name: round(component_scores[name] * WEIGHTS[name], 2)
        for name in WEIGHTS
    }

    total = round(sum(weighted_scores.values()), 2)

    return {
        "vendor": str(vendor).strip(),
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


def score_csv(path):
    results = []

    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row.")

        missing = [name for name in CSV_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise ValueError(
                "CSV is missing required column(s): " + ", ".join(missing)
            )

        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue

            try:
                result = score_vendor(
                    vendor=row["vendor"],
                    on_time_delivery=float(row["on_time_delivery"]),
                    defect_rate=float(row["defect_rate"]),
                    prepayment_exposure=float(row["prepayment_exposure"]),
                    compliance_incidents=int(row["compliance_incidents"]),
                    dependency_share=float(row["dependency_share"]),
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"CSV row {row_number}: {exc}") from exc

            results.append(result)

    if not results:
        raise ValueError("CSV file contains no vendor rows.")

    return results


def print_report(result):
    print()
    print(f"VENDOR RISK ENGINE v{VERSION}")
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


def print_batch_report(results):
    ranked = sorted(results, key=lambda item: item["score"], reverse=True)

    print()
    print(f"VENDOR RISK ENGINE v{VERSION} - PORTFOLIO")
    print("-" * 72)
    print(f"{'Vendor':30} {'Score':>8} {'Risk':>12}")
    print("-" * 72)

    for result in ranked:
        print(
            f"{result['vendor'][:30]:30} "
            f"{result['score']:8.2f} "
            f"{result['risk']:>12}"
        )

    print("-" * 72)
    print(f"Vendors scored      : {len(ranked)}")


def print_json(payload):
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Score supplier/vendor risk using transparent operational, "
            "commercial, compliance and dependency signals."
        )
    )

    parser.add_argument(
        "vendor",
        nargs="?",
        help="Vendor or supplier name for single-vendor scoring.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        help="Score a portfolio from a CSV file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return structured JSON instead of the text report.",
    )
    parser.add_argument(
        "--on-time-delivery",
        type=float,
        help="On-time delivery performance as a percentage (0-100).",
    )
    parser.add_argument(
        "--defect-rate",
        type=float,
        help="Defect rate as a percentage (0-100).",
    )
    parser.add_argument(
        "--prepayment-exposure",
        type=float,
        help="Buyer payment exposure before delivery as a percentage (0-100).",
    )
    parser.add_argument(
        "--compliance-incidents",
        type=int,
        help="Known compliance incidents in the review period.",
    )
    parser.add_argument(
        "--dependency-share",
        type=float,
        help="Share of category dependency concentrated on this vendor (0-100).",
    )

    return parser


def validate_cli_mode(parser, args):
    if args.csv_path and args.vendor:
        parser.error("use either a vendor name or --csv, not both.")

    if args.csv_path:
        return

    if not args.vendor:
        parser.error("vendor name is required unless --csv is used.")

    required = {
        "--on-time-delivery": args.on_time_delivery,
        "--defect-rate": args.defect_rate,
        "--prepayment-exposure": args.prepayment_exposure,
        "--compliance-incidents": args.compliance_incidents,
        "--dependency-share": args.dependency_share,
    }

    missing = [flag for flag, value in required.items() if value is None]
    if missing:
        parser.error(
            "single-vendor mode requires: " + ", ".join(missing)
        )


def main():
    parser = build_parser()
    args = parser.parse_args()
    validate_cli_mode(parser, args)

    try:
        if args.csv_path:
            results = score_csv(args.csv_path)
            if args.json:
                print_json(results)
            else:
                print_batch_report(results)
            return

        result = score_vendor(
            vendor=args.vendor,
            on_time_delivery=args.on_time_delivery,
            defect_rate=args.defect_rate,
            prepayment_exposure=args.prepayment_exposure,
            compliance_incidents=args.compliance_incidents,
            dependency_share=args.dependency_share,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.json:
        print_json(result)
    else:
        print_report(result)


if __name__ == "__main__":
    main()
