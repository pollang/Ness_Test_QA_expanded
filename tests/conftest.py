import json
import time
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from src.utils.emulator_launcher import start_emulators
from tests.constants import TEST_AMMETERS


@pytest.fixture(scope="session")
def running_emulators():
    """Starts real emulator instances on dedicated test ports (15001-15003),
    distinct from main.py's production/demo ports (5001-5003), for the life
    of the test session."""
    start_emulators(TEST_AMMETERS)
    time.sleep(1)  # let the emulator threads bind their sockets
    return TEST_AMMETERS


@pytest.fixture
def test_config_path(tmp_path):
    """Loads the static config/test_config.yaml (readable, checked into the repo),
    injects the canonical TEST_AMMETERS as the ammeters section (single source of
    truth, can't drift out of sync with tests/constants.py), and points
    results_dir at tmp_path (so tests never write into the real results/
    folder). Returns the path to the merged config, written to a temp file."""
    static_config_path = Path(__file__).parent.parent / "config" / "test_config.yaml"
    with open(static_config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["ammeters"] = TEST_AMMETERS
    config["result_management"]["results_dir"] = str(tmp_path / "results")

    path = tmp_path / "test_config.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)
    return str(path)


def pytest_sessionfinish(session, exitstatus):
    """Writes a human-diffable JSON summary of the test session into results/,
    alongside the machine-readable JUnit XML from --junitxml."""
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return

    stats = reporter.stats
    outcomes = {}
    for outcome, reports in stats.items():
        if not outcome:
            continue
        test_reports = [r for r in reports if getattr(r, "when", "call") == "call" or outcome in ("error",)]
        if test_reports:
            outcomes[outcome] = [r.nodeid for r in test_reports]

    summary = {
        "timestamp": datetime.now().isoformat(),
        "exit_status": exitstatus,
        "total": sum(len(v) for v in outcomes.values()),
        "passed": len(outcomes.get("passed", [])),
        "failed": len(outcomes.get("failed", [])),
        "skipped": len(outcomes.get("skipped", [])),
        "duration_seconds": time.time() - session.config._ammeter_session_start
        if hasattr(session.config, "_ammeter_session_start") else None,
        "outcomes": outcomes,
    }

    reports_dir = Path("results/pytest_reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    with open(reports_dir / f"pytest_summary_{stamp}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def pytest_sessionstart(session):
    session.config._ammeter_session_start = time.time()
