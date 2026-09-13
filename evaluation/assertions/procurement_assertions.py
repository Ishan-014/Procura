def assert_status(result, expected):
    actual = result.get("status")
    assert actual == expected, (
        f"Expected status {expected}, got {actual}"
    )


def assert_vendor(result, expected_vendor):
    vendor_result = result.get("vendor_result", {})
    actual = vendor_result.get("vendor_name")

    assert actual == expected_vendor, (
        f"Expected vendor {expected_vendor}, got {actual}"
    )


def assert_no_purchase_order(result):
    assert not result.get("purchase_order"), (
        "Purchase order should NOT have been created"
    )


def assert_purchase_order(result):
    assert result.get("purchase_order"), (
        "Purchase order should have been created"
    )


def assert_verification(result):
    verification = result.get("verification_result") or {}

    assert verification.get("verified") is True, (
        f"Verification failed: {verification}"
    )