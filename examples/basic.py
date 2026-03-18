"""Basic usage example for datadoc."""
from src.core import Datadoc

def main():
    instance = Datadoc(config={"verbose": True})

    print("=== datadoc Example ===\n")

    # Run primary operation
    result = instance.analyze(input="example data", mode="demo")
    print(f"Result: {result}")

    # Run multiple operations
    ops = ["analyze", "evaluate", "score]
    for op in ops:
        r = getattr(instance, op)(source="example")
        print(f"  {op}: {"✓" if r.get("ok") else "✗"}")

    # Check stats
    print(f"\nStats: {instance.get_stats()}")

if __name__ == "__main__":
    main()
