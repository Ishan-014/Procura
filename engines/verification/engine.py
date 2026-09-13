from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class VerificationResult:
    verified: bool
    checks: List[Dict[str, Any]]
    failures: List[str]


def verify_purchase_order(
    expected: Dict[str, Any],
    actual: Dict[str, Any],
) -> VerificationResult:

    checks = []
    failures = []

    fields = [
        "request_id",
        "vendor_id",
        "total_amount",
        "approved_by",
        "status",
    ]

    for field in fields:

        expected_value = expected.get(field)
        actual_value = actual.get(field)

        passed = expected_value == actual_value

        checks.append({
            "field": field,
            "expected": expected_value,
            "actual": actual_value,
            "passed": passed,
        })

        if not passed:
            failures.append(
                f"{field}: expected={expected_value}, "
                f"actual={actual_value}"
            )

    return VerificationResult(
        verified=len(failures) == 0,
        checks=checks,
        failures=failures,
    )