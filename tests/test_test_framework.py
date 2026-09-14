import pytest

from src.testing.test_framework import AmmeterTestFramework
from src.utils.emulator_launcher import AMMETER_CLASSES

AMMETER_TYPES = list(AMMETER_CLASSES)


@pytest.mark.integration
@pytest.mark.parametrize("ammeter_type", AMMETER_TYPES)
def test_run_test_session_end_to_end_per_ammeter(running_emulators, test_config_path, ammeter_type):
    framework = AmmeterTestFramework(config_path=test_config_path)
    result = framework.run_test_session(ammeter_type)

    assert result.ammeter_type == ammeter_type
    assert result.samples_requested > 0
    assert result.samples_collected == result.samples_requested
    assert result.errors == 0
