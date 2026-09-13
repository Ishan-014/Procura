from evaluation.scenarios import happy_path
from evaluation.scenarios import deadline_vendor
from evaluation.scenarios import duplicate_order
from evaluation.scenarios import budget_exceeded
from evaluation.scenarios import insufficient_inventory


SCENARIOS = [
    ("Happy Path", happy_path.run),
    ("Deadline Constraint", deadline_vendor.run),
    ("Duplicate Order", duplicate_order.run),
    ("Budget Exceeded", budget_exceeded.run),
    ("Insufficient Inventory", insufficient_inventory.run),
]


def main():
    passed = 0

    print("\n==============================")
    print("PROCURA EVALUATION")
    print("==============================\n")

    for name, scenario in SCENARIOS:
        try:
            scenario()
            print(f"PASS  ✓  {name}\n")
            passed += 1
        except Exception as e:
            print(f"FAIL  ✗  {name}")
            print(f"       {e}\n")

    print("==============================")
    print(f"RESULT: {passed}/{len(SCENARIOS)} passed")
    print("==============================\n")


if __name__ == "__main__":
    main()