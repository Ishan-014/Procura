import os

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleSheetsClient:

    def __init__(self):
        credentials_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE",
            "credentials/google-service-account.json",
        )

        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")

        if not spreadsheet_id:
            raise RuntimeError(
                "GOOGLE_SPREADSHEET_ID is not configured"
            )

        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES,
        )

        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open_by_key(spreadsheet_id)

    def get_budget(self, department: str):
        worksheet = self.sheet.worksheet("Budgets")
        rows = worksheet.get_all_records()

        for row in rows:
            if (
                str(row.get("Department", "")).strip().lower()
                == department.strip().lower()
            ):
                return float(row.get("Available Budget", 0))

        return None

    def get_existing_orders(self):
        worksheet = self.sheet.worksheet("Existing Orders")
        return worksheet.get_all_records()

    def record_purchase_order(self, purchase_order: dict):
        worksheet = self.sheet.worksheet("Existing Orders")

        item = purchase_order["items"][0]

        worksheet.append_row([
            purchase_order["id"],
            item["product_id"],
            item["quantity"],
            purchase_order["status"],
        ])

        return True

    # =========================
    # EVALUATION HELPERS
    # =========================

    def clear_existing_orders(self):
        worksheet = self.sheet.worksheet("Existing Orders")

        # Keep header row, remove test data
        worksheet.delete_rows(
            2,
            worksheet.row_count
        )

    def add_test_order(
        self,
        request_id: str,
        product_id: str,
        quantity: int,
        status: str = "APPROVED",
    ):
        worksheet = self.sheet.worksheet("Existing Orders")

        worksheet.append_row([
            request_id,
            product_id,
            quantity,
            status,
        ])

    def set_budget(
        self,
        department: str,
        amount: float,
    ):
        worksheet = self.sheet.worksheet("Budgets")
        rows = worksheet.get_all_records()

        for index, row in enumerate(rows, start=2):
            if (
                str(row.get("Department", "")).strip().lower()
                == department.strip().lower()
            ):
                worksheet.update_cell(
                    index,
                    2,
                    amount,
                )
                return

        worksheet.append_row([
            department,
            amount,
        ])