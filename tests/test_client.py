import pytest

from Ammeters.client import request_current_from_ammeter
from tests.constants import TEST_PORTS


@pytest.mark.integration
def test_client_receives_real_measurement(running_emulators, capsys):
    cfg = TEST_PORTS["greenlee"]
    request_current_from_ammeter(cfg["port"], cfg["command"].encode("utf-8"))
    captured = capsys.readouterr()
    assert "Received current measurement" in captured.out
    assert "No data received" not in captured.out


@pytest.mark.integration
def test_client_reports_no_data_on_mismatched_command(running_emulators, capsys):
    cfg = TEST_PORTS["greenlee"]
    wrong_command = cfg["command"].split(" ")[0].encode("utf-8")
    request_current_from_ammeter(cfg["port"], wrong_command)
    captured = capsys.readouterr()
    assert "No data received." in captured.out
