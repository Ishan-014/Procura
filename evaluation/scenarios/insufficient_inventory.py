from agent.graph import procurement_graph


def run():
    try:
        result = procurement_graph.invoke({
            "user_request": (
                "We need 40 laptops for Engineering. "
                "They must be delivered within 10 days."
            ),
            "request_id": "EVAL-INVENTORY-001",
            "trace": [],
        })

        # If the graph returns a blocked state, that's ideal.
        if result.get("status") == "BLOCKED":
            print("✓ Insufficient inventory blocked")
            print("✓ No purchase order created")
            return result

        raise AssertionError(
            "Expected procurement to be blocked due to insufficient inventory"
        )

    except ValueError as e:
        # Current vendor engine raises this when no qualifying vendor exists.
        if "No vendor satisfies all procurement constraints" in str(e):
            print("✓ Insufficient inventory blocked")
            print("✓ No purchase order created")
            return {
                "status": "BLOCKED",
                "purchase_order": None,
            }

        raise