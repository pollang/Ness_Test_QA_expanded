import argparse
import time
from datetime import datetime
from typing import Dict, List

from src.testing.models import TestResult
from src.testing.test_framework import AmmeterTestFramework
from src.testing.statistics_analyzer import StatisticsAnalyzer
from src.utils.emulator_launcher import start_emulators, AMMETER_CLASSES


def parse_args():
    parser = argparse.ArgumentParser(description="Config-driven ammeter test runner.")
    parser.add_argument("--ammeter", choices=[*AMMETER_CLASSES, "all"], default="all")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--no-plot", action="store_true", help="Disable visualization even if config enables it.")
    parser.add_argument("--compare", action="store_true", help="Print a cross-ammeter comparison table (requires more than one ammeter run).")
    parser.add_argument("--history", action="store_true",
                         help="Show archived past results instead of running new samples. "
                              "Combine with --compare to compare the most recent archived run per ammeter.")
    return parser.parse_args()


def print_result(ammeter_type: str, result: TestResult) -> None:
    print(f"\n=== {ammeter_type} ===")
    print(f"  run_id:            {result.run_id}")
    print(f"  samples collected: {result.samples_collected}/{result.samples_requested} (errors: {result.errors})")
    print("  statistics:")
    for metric, value in result.statistics.items():
        print(f"    {metric:>8}: {value}")
    if result.plot_path:
        print(f"  plot saved to: {result.plot_path}")


def print_history(framework: AmmeterTestFramework, ammeter_type: str) -> List[TestResult]:
    """Prints every archived run for one ammeter type (oldest first, since run_ids
    are timestamp-based and list_results() sorts by filename). Returns the list."""
    records = framework.result_manager.list_results(ammeter_type)
    print(f"\n=== History for {ammeter_type} ({len(records)} run(s) found) ===")
    if not records:
        print("  (none)")
        return records

    header = f"  {'run_id':<32} {'timestamp':<26} {'mean':>10} {'median':>10} {'stdev':>10} {'CV':>8} {'samples':>7}"
    print(header)
    for r in records:
        stats = r.statistics or {}
        mean = stats.get("mean") or 0.0
        stdev = stats.get("stdev") or 0.0
        # Prefer the stored metric (now part of the default statistical_metrics list);
        # fall back to computing it for older archived results saved before this metric existed.
        cv = stats.get("coefficient_of_variation")
        if cv is None:
            cv = (stdev / mean) if mean else float("inf")
        print(f"  {r.run_id:<32} {r.timestamp:<26} {mean:>10.4f} "
              f"{(stats.get('median') or 0.0):>10.4f} {stdev:>10.4f} {cv:>8.3f} {r.samples_collected:>7}")
    return records


def print_and_save_comparison(framework: AmmeterTestFramework, results_by_ammeter: Dict[str, TestResult], source: str) -> None:
    label = "Cross-ammeter comparison" if source == "live" else "Historical comparison (most recent archived run per ammeter)"
    print(f"\n=== {label} (sorted by precision: lowest coefficient of variation first) ===")
    print("Note: no reference/calibrated current is available, so this measures precision")
    print("(consistency of repeated readings), not accuracy (closeness to a true value).")
    comparison = StatisticsAnalyzer.compare(results_by_ammeter)
    print(comparison.to_string())

    most_precise = comparison.index[0]
    most_precise_cv = comparison.loc[most_precise, "coefficient_of_variation"]
    conclusion = (f"Most precise/consistent measurement method: '{most_precise}' "
                  f"(coefficient of variation = {most_precise_cv:.3f}, lowest among the ammeters compared). "
                  f"This reflects measurement precision, not accuracy - see the note above.")
    print(f"\nConclusion: {conclusion}")

    comparison_record = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "ammeter_run_ids": {ammeter_type: result.run_id for ammeter_type, result in results_by_ammeter.items()},
        "comparison": comparison.reset_index().to_dict(orient="records"),
        "conclusion": conclusion,
        "most_precise_ammeter": most_precise,
    }
    saved_path = framework.result_manager.save_comparison(comparison_record)
    print(f"\nComparison saved to: {saved_path}")


def run_history(framework: AmmeterTestFramework, ammeter_types: list, do_compare: bool) -> None:
    latest_by_ammeter = {}
    for ammeter_type in ammeter_types:
        records = print_history(framework, ammeter_type)
        if records:
            latest_by_ammeter[ammeter_type] = records[-1]

    if do_compare:
        if len(latest_by_ammeter) > 1:
            print_and_save_comparison(framework, latest_by_ammeter, source="historical")
        else:
            print("\n(Skipping historical comparison: fewer than 2 ammeter types have archived results.)")


def run_live(framework: AmmeterTestFramework, ammeter_types: list, do_compare: bool) -> None:
    start_emulators(framework.config["ammeters"])
    time.sleep(1)  # let the emulator threads bind their sockets

    results = {}
    for ammeter_type in ammeter_types:
        print(f"Testing {ammeter_type} ammeter...")
        result = framework.run_test_session(ammeter_type)
        results[ammeter_type] = result
        print_result(ammeter_type, result)

    if do_compare and len(results) > 1:
        print_and_save_comparison(framework, results, source="live")


def main():
    args = parse_args()
    framework = AmmeterTestFramework(config_path=args.config)

    if args.no_plot:
        framework.config.setdefault("analysis", {}).setdefault("visualization", {})["enabled"] = False

    ammeter_types = list(framework.config["ammeters"]) if args.ammeter == "all" else [args.ammeter]

    if args.history:
        run_history(framework, ammeter_types, args.compare)
    else:
        run_live(framework, ammeter_types, args.compare)


if __name__ == "__main__":
    main()
