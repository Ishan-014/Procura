import os
import requests


SLACK_API = "https://slack.com/api"


class SlackClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")

        if not self.token:
            raise RuntimeError("SLACK_BOT_TOKEN is not configured")

    def _request(self, method: str, payload: dict):
        response = requests.post(
            f"{SLACK_API}/{method}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Slack API error: {data.get('error', 'unknown_error')}"
            )

        return data

    def send_message(self, channel: str, text: str):
        return self._request(
            "chat.postMessage",
            {
                "channel": channel,
                "text": text,
            },
        )

    def send_approval_request(
        self,
        channel: str,
        request_id: str,
        vendor_name: str,
        amount: float,
        reason: str,
        approval_url: str,
    ):
        text = (
            "🔔 PROCURA PROCUREMENT APPROVAL\n\n"
            f"Request: {request_id}\n"
            f"Vendor: {vendor_name}\n"
            f"Amount: ₹{amount:,.2f}\n\n"
            f"Reason: {reason}\n\n"
            "CEO approval is required before execution.\n\n"
            f"👉 APPROVE: {approval_url}"
        )

        return self.send_message(channel, text)