from agent.graph import procurement_graph
from evaluation.assertions.procurement_assertions import (
    assert_status,
    assert_no_purchase_order,
)
from evaluation.seeders.google_sheets import (
    seed_budget_exceeded,
    restore_budget,
)


def run():
    seed_budget_exceeded()

    try:
        result = procurement_graph.invoke({
            "user_request": (
                "We need 30 laptops for Engineering. "
                "They must be delivered within 10 days."
            ),
            "request_id": "EVAL-BUDGET-001",
            "trace": [],
        })

        assert_status(result, "BLOCKED")
        assert_no_purchase_order(result)

        print("✓ Budget limit enforced")
        print("✓ No purchase order created")

        return result

    finally:
        restore_budget()