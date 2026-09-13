from agent.graph import procurement_graph


result = procurement_graph.invoke({
    "user_request": """
    We need 30 laptops for the engineering team.
    They are required within 10 days.
    """,
    "trace": [],
})


print("\n=== PROCURA GRAPH ===")

print("\nSTATUS:")
print(result.get("status"))

print("\nREQUEST:")
print(result.get("request"))

print("\nTRACE:")
for step in result.get("trace", []):
    print(" -", step)