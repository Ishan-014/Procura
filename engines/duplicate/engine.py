from dataclasses import dataclass
from typing import List


@dataclass
class ExistingOrder:
    request_id: str
    product_id: str
    quantity: int
    status: str


@dataclass
class DuplicateDecision:
    is_duplicate: bool
    existing_quantity: int
    additional_quantity: int
    reason: str


ACTIVE_STATUSES = {
    "APPROVED",
    "CREATED",
    "PROCESSING",
}


def check_duplicate(
    product_id: str,
    requested_quantity: int,
    existing_orders: List[ExistingOrder],
) -> DuplicateDecision:

    existing_quantity = 0

    # Calculate how many units of this product
    # are already covered by active orders.
    for order in existing_orders:

        if (
            order.product_id.strip().upper() == product_id.strip().upper()
            and order.status.strip().upper() in ACTIVE_STATUSES
        ):
            existing_quantity += max(0, int(order.quantity))

    # Case 1:
    # Existing orders completely cover the request.
    if existing_quantity >= requested_quantity:

        return DuplicateDecision(
            is_duplicate=True,
            existing_quantity=existing_quantity,
            additional_quantity=0,
            reason=(
                f"Existing orders already cover "
                f"{existing_quantity} units. "
                f"No additional purchase is required."
            ),
        )

    # Case 2:
    # Some units already exist, but more are required.
    if existing_quantity > 0:

        additional_quantity = (
            requested_quantity - existing_quantity
        )

        return DuplicateDecision(
            is_duplicate=False,
            existing_quantity=existing_quantity,
            additional_quantity=additional_quantity,
            reason=(
                f"Existing orders cover {existing_quantity} units. "
                f"{additional_quantity} additional units are required."
            ),
        )

    # Case 3:
    # No existing order for this product.
    return DuplicateDecision(
        is_duplicate=False,
        existing_quantity=0,
        additional_quantity=requested_quantity,
        reason=(
            "No matching active order found. "
            "The full requested quantity is required."
        ),
    )