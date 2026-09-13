"""Minimal usage example for AmmeterTestFramework. For the fuller config-driven
CLI (ammeter selection, --compare, --no-plot), see run_test_suite.py instead.

Run from the repo root as a module (not directly), so the "src"/"Ammeters"
packages resolve on sys.path:
    python -m examples.run_tests
"""

import time

from src.testing.test_framework import AmmeterTestFramework
from src.utils.emulator_launcher import start_emulators


def main():
    framework = AmmeterTestFramework()
    start_emulators(framework.config["ammeters"])
    time.sleep(1)

    for ammeter_type in framework.config["ammeters"]:
        print(f"Testing {ammeter_type} ammeter...")
        result = framework.run_test(ammeter_type)
        print(f"Results for {ammeter_type}: {result['statistics']}")


if __name__ == "__main__":
    main()
