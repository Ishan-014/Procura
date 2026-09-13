from engines.policy.engine import evaluate_policy
from engines.budget.engine import check_budget
from engines.duplicate.engine import (
    check_duplicate,
    ExistingOrder,
)
from engines.vendor.engine import (
    select_vendor,
    VendorCandidate,
)


def test_policy_manager():
    result = evaluate_policy(50_000)

    assert result.allowed is True
    assert result.required_approver == "MANAGER"


def test_policy_cto():
    result = evaluate_policy(1_000_000)

    assert result.allowed is True
    assert result.required_approver == "CTO"


def test_policy_ceo():
    result = evaluate_policy(2_000_000)

    assert result.allowed is True
    assert result.required_approver == "CEO"


def test_budget_pass():
    result = check_budget(
        available_budget=5_000_000,
        requested_amount=2_000_000,
    )

    assert result.within_budget is True
    assert result.remaining_budget == 3_000_000


def test_budget_fail():
    result = check_budget(
        available_budget=1_000_000,
        requested_amount=2_000_000,
    )

    assert result.within_budget is False


def test_duplicate():
    orders = [
        ExistingOrder(
            request_id="REQ-1",
            product_id="P001",
            quantity=30,
            status="APPROVED",
        )
    ]

    result = check_duplicate(
        product_id="P001",
        requested_quantity=30,
        existing_orders=orders,
    )

    assert result.is_duplicate is True
    assert result.additional_quantity == 0


def test_partial_order():
    orders = [
        ExistingOrder(
            request_id="REQ-1",
            product_id="P001",
            quantity=10,
            status="APPROVED",
        )
    ]

    result = check_duplicate(
        product_id="P001",
        requested_quantity=30,
        existing_orders=orders,
    )

    assert result.is_duplicate is False
    assert result.existing_quantity == 10
    assert result.additional_quantity == 20


def test_vendor_selection():
    candidates = [
        VendorCandidate(
            vendor_id="V001",
            vendor_name="Vendor A",
            approved=True,
            unit_price=72_000,
            quantity_available=30,
            delivery_days=3,
            warranty_years=3,
            rating=4.7,
        ),
        VendorCandidate(
            vendor_id="V002",
            vendor_name="Vendor B",
            approved=True,
            unit_price=65_000,
            quantity_available=50,
            delivery_days=18,
            warranty_years=2,
            rating=4.4,
        ),
        VendorCandidate(
            vendor_id="V003",
            vendor_name="Vendor C",
            approved=True,
            unit_price=69_500,
            quantity_available=30,
            delivery_days=7,
            warranty_years=3,
            rating=4.6,
        ),
    ]

    result = select_vendor(
        candidates=candidates,
        quantity=30,
        max_delivery_days=10,
    )

    assert result.vendor_id == "V003"
    assert result.total_cost == 2_085_000