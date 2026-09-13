from dataclasses import dataclass
from typing import List


@dataclass
class VendorCandidate:
    vendor_id: str
    vendor_name: str
    approved: bool
    unit_price: float
    quantity_available: int
    delivery_days: int
    warranty_years: int
    rating: float


@dataclass
class VendorDecision:
    vendor_id: str
    vendor_name: str
    total_cost: float
    reason: str


def select_vendor(
    candidates: List[VendorCandidate],
    quantity: int,
    max_delivery_days: int,
) -> VendorDecision:

    # --------------------------------------------------------
    # NORMALIZE INPUTS
    # --------------------------------------------------------

    quantity = int(quantity)
    max_delivery_days = int(max_delivery_days)

    # --------------------------------------------------------
    # APPLY PROCUREMENT CONSTRAINTS
    # --------------------------------------------------------

    eligible = []

    for vendor in candidates:

        # Vendor must be approved.
        if not vendor.approved:
            continue

        # Vendor must have enough inventory.
        if vendor.quantity_available < quantity:
            continue

        # Vendor must meet required delivery deadline.
        if vendor.delivery_days > max_delivery_days:
            continue

        eligible.append(vendor)

    # --------------------------------------------------------
    # NO VALID VENDOR
    # --------------------------------------------------------

    if not eligible:
        raise ValueError(
            "No vendor satisfies all procurement constraints."
        )

    # --------------------------------------------------------
    # DETERMINISTIC RANKING
    #
    # Cheapest qualifying vendor wins.
    # Earlier delivery breaks ties.
    # Longer warranty breaks remaining ties.
    # --------------------------------------------------------

    eligible.sort(
        key=lambda vendor: (
            vendor.unit_price,
            vendor.delivery_days,
            -vendor.warranty_years,
            -vendor.rating,
        )
    )

    selected = eligible[0]

    total_cost = selected.unit_price * quantity

    reason = (
        f"{selected.vendor_name} selected as the lowest-cost "
        f"approved vendor that satisfies all constraints: "
        f"{quantity} units available, "
        f"{selected.delivery_days}-day delivery, "
        f"{selected.warranty_years}-year warranty."
    )

    return VendorDecision(
        vendor_id=selected.vendor_id,
        vendor_name=selected.vendor_name,
        total_cost=total_cost,
        reason=reason,
    )