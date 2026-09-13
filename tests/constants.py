"""Shared test-port/command constants for the SUT test suite, used by both
conftest.py and the test modules."""

from src.utils.emulator_launcher import AMMETER_CLASSES

TEST_PORTS = {
    "greenlee": {"port": 15001, "command": "MEASURE_GREENLEE -get_measurement"},
    "entes": {"port": 15002, "command": "MEASURE_ENTES -get_data"},
    "circutor": {"port": 15003, "command": "MEASURE_CIRCUTOR -get_measurement -current"},
}

# Ports/commands are legitimately test-specific data (can't be derived from the
# production registry), but the set of ammeter types must never silently drift
# from it - fail fast at import time rather than quietly testing a stale subset.
assert set(TEST_PORTS) == set(AMMETER_CLASSES), (
    f"TEST_PORTS keys {set(TEST_PORTS)} must match AMMETER_CLASSES keys {set(AMMETER_CLASSES)}"
)
