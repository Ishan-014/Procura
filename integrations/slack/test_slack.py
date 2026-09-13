from dotenv import load_dotenv
import os

from integrations.slack.client import SlackClient


load_dotenv()


channel = os.getenv("SLACK_APPROVAL_CHANNEL")

if not channel:
    raise RuntimeError("SLACK_APPROVAL_CHANNEL is not configured")

client = SlackClient()

result = client.send_message(
    channel,
    "🚀 Procura integration test: Slack is connected."
)

print("SLACK OK")
print(result)