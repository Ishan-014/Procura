from dataclasses import dataclass
from typing import Optional


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    required_approver: Optional[str]


# Procurement policy.
# Later this will be loaded from the company's policy document.
APPROVAL_RULES = [
    {
        "max_amount": 100_000,
        "approver": "MANAGER",
    },
    {
        "max_amount": 500_000,
        "approver": "DEPARTMENT_HEAD",
    },
    {
        "max_amount": 1_500_000,
        "approver": "CTO",
    },
    {
        "max_amount": None,
        "approver": "CEO",
    },
]


def evaluate_policy(amount: float) -> PolicyDecision:
    """
    Determine whether a purchase is allowed
    and which approval authority is required.
    """

    if amount <= 0:
        return PolicyDecision(
            allowed=False,
            reason="Purchase amount must be greater than zero.",
            required_approver=None,
        )

    for rule in APPROVAL_RULES:
        max_amount = rule["max_amount"]

        if max_amount is None or amount <= max_amount:
            return PolicyDecision(
                allowed=True,
                reason="Purchase falls within procurement policy.",
                required_approver=rule["approver"],
            )

    return PolicyDecision(
        allowed=False,
        reason="Purchase does not satisfy procurement policy.",
        required_approver=None,
    )