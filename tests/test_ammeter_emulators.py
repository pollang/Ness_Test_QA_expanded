import socket

import pytest

from src.utils.emulator_launcher import AMMETER_CLASSES
from tests.constants import TEST_PORTS

# Derived from the same registry emulator_launcher.py uses, so a new ammeter
# type added there is automatically covered here too.
AMMETER_CASES = list(AMMETER_CLASSES.items())


@pytest.mark.unit
@pytest.mark.parametrize("ammeter_type,ammeter_cls", AMMETER_CASES)
def test_get_current_command_matches_config(ammeter_type, ammeter_cls):
    ammeter = ammeter_cls(port=0)
    expected_command = TEST_PORTS[ammeter_type]["command"].encode("utf-8")
    assert ammeter.get_current_command == expected_command


def _query(port: int, command: bytes, timeout: float = 2.0) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(("localhost", port))
        s.sendall(command)
        return s.recv(1024)


@pytest.mark.integration
@pytest.mark.parametrize("ammeter_type,_cls", AMMETER_CASES)
def test_exact_command_match_returns_data(running_emulators, ammeter_type, _cls):
    port = TEST_PORTS[ammeter_type]["port"]
    command = TEST_PORTS[ammeter_type]["command"].encode("utf-8")
    data = _query(port, command)
    assert data, f"{ammeter_type}: expected a measurement, got no data"
    float(data.decode("utf-8"))  # must parse as a valid current reading


@pytest.mark.integration
@pytest.mark.parametrize("ammeter_type,_cls", AMMETER_CASES)
def test_mismatched_command_returns_no_data(running_emulators, ammeter_type, _cls):
    port = TEST_PORTS[ammeter_type]["port"]
    wrong_command = TEST_PORTS[ammeter_type]["command"].split(" ")[0].encode("utf-8")  # e.g. b"MEASURE_GREENLEE"
    data = _query(port, wrong_command)
    assert data == b"", f"{ammeter_type}: expected no data for a mismatched command, got {data!r}"
