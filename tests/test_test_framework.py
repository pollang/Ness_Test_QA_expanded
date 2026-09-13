import pytest

from src.testing.test_framework import AmmeterTestFramework

AMMETER_TYPES = ["greenlee", "entes", "circutor"]


@pytest.mark.integration
@pytest.mark.parametrize("ammeter_type", AMMETER_TYPES)
def test_run_test_end_to_end_per_ammeter(running_emulators, test_config_path, ammeter_type):
    framework = AmmeterTestFramework(config_path=test_config_path)
    result = framework.run_test(ammeter_type)

    assert result["ammeter_type"] == ammeter_type
    assert result["samples_collected"] == result["samples_requested"] == 3
    assert result["errors"] == 0


@pytest.mark.integration
def test_run_test_unknown_ammeter_raises_value_error(running_emulators, test_config_path):
    framework = AmmeterTestFramework(config_path=test_config_path)
    with pytest.raises(ValueError):
        framework.run_test("nonexistent")
