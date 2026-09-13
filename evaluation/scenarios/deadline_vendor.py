from agent.graph import procurement_graph
from evaluation.assertions.procurement_assertions import (
    assert_status,
    assert_vendor,
)


def run():
    result = procurement_graph.invoke({
        "user_request": (
            "We need 30 laptops for Engineering. "
            "They must be delivered within 10 days. "
            "Choose the best qualifying vendor."
        ),
        "request_id": "EVAL-DEADLINE-001",
        "trace": [],
    })

    assert_vendor(result, "Vendor C")

    print("✓ Cheapest vendor rejected because of deadline")
    print("✓ Vendor C selected")

    return result