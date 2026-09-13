from integrations.google_sheets.client import GoogleSheetsClient


def clean_sheet():
    client = GoogleSheetsClient()
    client.clear_existing_orders()


def seed_duplicate():
    client = GoogleSheetsClient()

    client.clear_existing_orders()

    client.add_test_order(
        request_id="EVAL-DUPLICATE-ORDER",
        product_id="P001",
        quantity=30,
        status="APPROVED",
    )


def seed_budget_exceeded():
    client = GoogleSheetsClient()

    client.set_budget(
        department="Engineering",
        amount=1_000_000,
    )


def restore_budget():
    client = GoogleSheetsClient()

    client.set_budget(
        department="Engineering",
        amount=5_000_000,
    )