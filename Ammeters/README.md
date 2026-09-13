# Ammeter Emulators

This project provides emulators for different types of ammeters: Greenlee, ENTES, and CIRCUTOR. Each ammeter emulator runs on a separate thread and can respond to current measurement requests.

## Project Structure

- `Ammeters/`
  - `base_ammeter.py`: Base class for all ammeter emulators.
  - `Greenlee_Ammeter.py`: Emulator for the Greenlee ammeter.
  - `Entes_Ammeter.py`: Emulator for the ENTES ammeter.
  - `Circutor_Ammeter.py`: Emulator for the CIRCUTOR ammeter.
  - `client.py`: Client to request current measurements from the ammeter emulators.

(For `main.py`, `config/`, `src/`, and the rest of the testing framework built around these emulators, see the top-level [README.md](../README.md).)

## Usage

### Greenlee Ammeter

- **Port**: 5001
- **Command**: `MEASURE_GREENLEE -get_measurement`
- **Measurement Logic**: Calculates current using voltage (1V - 10V) and resistance (0.1Ω - 100Ω).
- **Measurement method**: Ohm's Law: I = V / R

### ENTES Ammeter

- **Port**: 5002
- **Command**: `MEASURE_ENTES -get_data`
- **Measurement Logic**: Calculates current using magnetic field strength (0.01T - 0.1T) and calibration factor (500 - 2000).
- **Measurement method**: Hall Effect: I = B * K

### CIRCUTOR Ammeter

- **Port**: 5003
- **Command**: `MEASURE_CIRCUTOR -get_measurement -current`
- **Measurement Logic**: Calculates current using voltage values (0.1V - 1.0V) over 10 samples and a random time step (0.001s - 0.01s).
- **Measurement method**: Rogowski Coil Integration: I = Σ(V·Δt)

To start the ammeter emulators and request one current measurement from each, run the `main.py` script from the repo root:
```sh
python main.py
```
