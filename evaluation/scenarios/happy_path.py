from agent.graph import procurement_graph
from evaluation.assertions.procurement_assertions import (
    assert_status,
    assert_vendor,
    assert_purchase_order,
    assert_verification,
)


def run():
    result = procurement_graph.invoke({
        "user_request": (
            "We need 30 laptops for Engineering. "
            "They must be delivered within 10 days. "
            "Find the best option under company policy "
            "and handle the purchase."
        ),
        "request_id": "EVAL-HAPPY-001",
        "trace": [],
    })

    # Before approval, the agent should stop safely.
    assert_status(result, "AWAITING_APPROVAL")
    assert_vendor(result, "Vendor C")

    print("✓ Correct vendor")
    print("✓ Human approval required")

    return result