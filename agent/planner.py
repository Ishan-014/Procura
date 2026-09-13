import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


PLANNER_PROMPT = """
You are the request-understanding component of Procura,
an AI procurement agent.

Your job is ONLY to convert the user's natural-language
procurement request into structured JSON.

Do NOT:
- choose a vendor
- calculate the final procurement decision
- approve a purchase
- invent missing information
- assume a budget
- assume a deadline

If information is missing, use null.

Return ONLY valid JSON with exactly these fields:

{
  "product_name": string or null,
  "quantity": integer or null,
  "department": string or null,
  "required_by_days": integer or null,
  "requester_role": string or null,
  "available_budget": number or null
}

Interpret relative deadlines such as:
"within 10 days" -> 10

Example:

User:
"We need 30 laptops for the engineering team within 10 days."

Output:
{
  "product_name": "laptop",
  "quantity": 30,
  "department": "Engineering",
  "required_by_days": 10,
  "requester_role": null,
  "available_budget": null
}

"""


def plan_request(user_request: str) -> dict:
    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": PLANNER_PROMPT,
            },
            {
                "role": "user",
                "content": user_request,
            },
        ],
    )

    text = response.output_text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Planner returned invalid JSON: {text}"
        ) from exc

    required_fields = {
        "product_name",
        "quantity",
        "department",
        "required_by_days",
        "requester_role",
        "available_budget",
    }

    if set(result.keys()) != required_fields:
        raise RuntimeError(
            f"Planner returned unexpected fields: {result}"
        )

    return result