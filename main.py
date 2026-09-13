import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter


def run_emulator(ammeter):
    ammeter.start_server()

if __name__ == "__main__":
    # Start each ammeter in a separate thread
    greenlee = GreenleeAmmeter(5001)
    entes = EntesAmmeter(5002)
    circutor = CircutorAmmeter(5003)

    threading.Thread(target=run_emulator, args=(greenlee,), daemon=True).start()
    threading.Thread(target=run_emulator, args=(entes,), daemon=True).start()
    threading.Thread(target=run_emulator, args=(circutor,), daemon=True).start()

    # Wait for the servers to start, if you have problem restarting the servers between runs try increasing sleep time.
    time.sleep(5)
    request_current_from_ammeter(5001, greenlee.get_current_command)  # Request from Greenlee Ammeter
    request_current_from_ammeter(5002, entes.get_current_command)  # Request from ENTES Ammeter
    request_current_from_ammeter(5003, circutor.get_current_command)  # Request from CIRCUTOR Ammeter
