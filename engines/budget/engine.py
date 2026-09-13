from dataclasses import dataclass


@dataclass
class BudgetDecision:
    within_budget: bool
    available_budget: float
    requested_amount: float
    remaining_budget: float
    reason: str


def check_budget(
    available_budget: float,
    requested_amount: float,
) -> BudgetDecision:

    remaining = available_budget - requested_amount

    if requested_amount <= available_budget:
        return BudgetDecision(
            within_budget=True,
            available_budget=available_budget,
            requested_amount=requested_amount,
            remaining_budget=remaining,
            reason="Purchase is within available budget.",
        )

    return BudgetDecision(
        within_budget=False,
        available_budget=available_budget,
        requested_amount=requested_amount,
        remaining_budget=remaining,
        reason="Purchase exceeds available budget.",
    )