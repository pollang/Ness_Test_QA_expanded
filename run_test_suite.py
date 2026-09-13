import argparse
import time

from src.testing.test_framework import AmmeterTestFramework
from src.testing.statistics_analyzer import StatisticsAnalyzer
from src.utils.emulator_launcher import start_emulators


def parse_args():
    parser = argparse.ArgumentParser(description="Config-driven ammeter test runner.")
    parser.add_argument("--ammeter", choices=["greenlee", "entes", "circutor", "all"], default="all")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--no-plot", action="store_true", help="Disable visualization even if config enables it.")
    parser.add_argument("--compare", action="store_true", help="Print a cross-ammeter comparison table (requires more than one ammeter run).")
    return parser.parse_args()


def print_result(ammeter_type: str, result: dict) -> None:
    print(f"\n=== {ammeter_type} ===")
    print(f"  run_id:            {result['run_id']}")
    print(f"  samples collected: {result['samples_collected']}/{result['samples_requested']} (errors: {result['errors']})")
    print("  statistics:")
    for metric, value in result["statistics"].items():
        print(f"    {metric:>8}: {value}")
    if result.get("plot_path"):
        print(f"  plot saved to: {result['plot_path']}")


def main():
    args = parse_args()
    framework = AmmeterTestFramework(config_path=args.config)

    if args.no_plot:
        framework.config.setdefault("analysis", {}).setdefault("visualization", {})["enabled"] = False

    start_emulators(framework.config["ammeters"])
    time.sleep(1)  # let the emulator threads bind their sockets

    ammeter_types = list(framework.config["ammeters"]) if args.ammeter == "all" else [args.ammeter]

    results = {}
    for ammeter_type in ammeter_types:
        print(f"Testing {ammeter_type} ammeter...")
        result = framework.run_test(ammeter_type)
        results[ammeter_type] = result
        print_result(ammeter_type, result)

    if args.compare and len(results) > 1:
        print("\n=== Cross-ammeter comparison (sorted by precision: lowest coefficient of variation first) ===")
        print("Note: no reference/calibrated current is available, so this measures precision")
        print("(consistency of repeated readings), not accuracy (closeness to a true value).")
        comparison = StatisticsAnalyzer.compare(results)
        print(comparison.to_string())


if __name__ == "__main__":
    main()
