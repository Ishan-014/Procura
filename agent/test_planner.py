from planner import plan_request


request = """
We need 30 laptops for the engineering team.
They are required within 10 days.
"""


result = plan_request(request)

print("\nPLANNER RESULT")
print("================")
for key, value in result.items():
    print(f"{key}: {value}")