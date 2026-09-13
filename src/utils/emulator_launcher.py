import threading
from typing import Dict

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter

_AMMETER_CLASSES = {
    "greenlee": GreenleeAmmeter,
    "entes": EntesAmmeter,
    "circutor": CircutorAmmeter,
}


def start_emulators(ammeters_config: Dict[str, dict]) -> None:
    """
    Starts one daemon-thread emulator per entry in ammeters_config
    (as loaded from config.yaml's `ammeters` section), e.g.:
        {"greenlee": {"port": 5001, ...}, "entes": {"port": 5002, ...}}
    Emulators run for the life of the process; there is no stop/restart
    (AmmeterEmulatorBase.start_server() has no clean shutdown mechanism).
    """
    for ammeter_type, cfg in ammeters_config.items():
        ammeter_cls = _AMMETER_CLASSES.get(ammeter_type)
        if ammeter_cls is None:
            raise ValueError(f"Unknown ammeter_type '{ammeter_type}', expected one of {list(_AMMETER_CLASSES)}")
        ammeter = ammeter_cls(cfg["port"])
        threading.Thread(target=ammeter.start_server, daemon=True).start()
