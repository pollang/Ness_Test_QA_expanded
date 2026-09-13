import json
import time
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from src.utils.emulator_launcher import start_emulators
from tests.constants import TEST_PORTS


@pytest.fixture(scope="session")
def running_emulators():
    """Starts real emulator instances on dedicated test ports (15001-15003),
    distinct from main.py's production/demo ports (5001-5003), for the life
    of the test session."""
    start_emulators(TEST_PORTS)
    time.sleep(1)  # let the emulator threads bind their sockets
    return TEST_PORTS


@pytest.fixture
def test_config_path(tmp_path):
    """A config.yaml pointing at the test-port emulators with fast sampling,
    so end-to-end tests don't touch the real config/config.yaml."""
    config = {
        "testing": {
            "sampling": {
                "measurements_count": 3,
                "total_duration_seconds": 5,
                "sampling_frequency_hz": 20,
            },
        },
        "ammeters": TEST_PORTS,
        "analysis": {
            "statistical_metrics": ["mean", "median", "stdev", "min", "max"],
            "visualization": {"enabled": False, "plot_types": []},
        },
        "result_management": {"results_dir": str(tmp_path / "results"), "keep_raw_readings": True},
    }
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
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(reports_dir / f"{stamp}_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def pytest_sessionstart(session):
    session.config._ammeter_session_start = time.time()
