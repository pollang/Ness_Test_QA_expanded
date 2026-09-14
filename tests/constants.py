"""Shared test-port/command constants for the SUT test suite, used by both
conftest.py and the test modules."""

from src.utils.emulator_launcher import AMMETER_CLASSES

TEST_AMMETERS = {
    "greenlee": {"port": 15001, "command": "MEASURE_GREENLEE -get_measurement"},
    "entes": {"port": 15002, "command": "MEASURE_ENTES -get_data"},
    "circutor": {"port": 15003, "command": "MEASURE_CIRCUTOR -get_measurement -current"},
}

assert set(TEST_AMMETERS) == set(AMMETER_CLASSES), (
    f"TEST_AMMETERS keys {set(TEST_AMMETERS)} must match AMMETER_CLASSES keys {set(AMMETER_CLASSES)}"
)
