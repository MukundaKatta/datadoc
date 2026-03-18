"""CLI for datadoc."""
import sys, json, argparse
from .core import Datadoc

def main():
    parser = argparse.ArgumentParser(description="DataDoc — AI Data Quality Auditor. Automated data quality assessment, profiling, and cleaning.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Datadoc()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.analyze(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"datadoc v0.1.0 — DataDoc — AI Data Quality Auditor. Automated data quality assessment, profiling, and cleaning.")

if __name__ == "__main__":
    main()
