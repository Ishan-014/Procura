import os

from dotenv import load_dotenv
from notion_client import Client


# Load variables from E:\procura\.env
load_dotenv()


class NotionClient:

    def __init__(self):
        token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("NOTION_DATABASE_ID")

        if not token:
            raise RuntimeError("NOTION_TOKEN is not configured")

        if not database_id:
            raise RuntimeError("NOTION_DATABASE_ID is not configured")

        self.client = Client(auth=token)
        self.database_id = database_id

    def record_procurement(self, state: dict):
        """
        Record a completed procurement in the Notion audit database.
        """

        request_id = state["request_id"]
        vendor = state["vendor_result"]
        verification = state.get("verification_result", {})

        self.client.pages.create(
            parent={
                "database_id": self.database_id
            },
            properties={
                "Request ID": {
                    "title": [
                        {
                            "text": {
                                "content": request_id
                            }
                        }
                    ]
                },
                "Vendor": {
                    "rich_text": [
                        {
                            "text": {
                                "content": vendor["vendor_name"]
                            }
                        }
                    ]
                },
                "Amount": {
                    "number": vendor["total_cost"]
                },
                "Status": {
                    "rich_text": [
                        {
                            "text": {
                                "content": state.get(
                                    "status",
                                    "UNKNOWN"
                                )
                            }
                        }
                    ]
                },
                "Decision": {
                    "rich_text": [
                        {
                            "text": {
                                "content": vendor.get(
                                    "reason",
                                    ""
                                )
                            }
                        }
                    ]
                },
                "Verified": {
                    "checkbox": verification.get(
                        "verified",
                        False
                    )
                },
            },
        )

        return True