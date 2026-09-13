"""Shared test-port/command constants for the SUT test suite, used by both
conftest.py and the test modules."""

TEST_PORTS = {
    "greenlee": {"port": 15001, "command": "MEASURE_GREENLEE -get_measurement"},
    "entes": {"port": 15002, "command": "MEASURE_ENTES -get_data"},
    "circutor": {"port": 15003, "command": "MEASURE_CIRCUTOR -get_measurement -current"},
}
