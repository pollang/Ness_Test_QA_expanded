# Ammeter Testing Framework — Usage Instructions

A unified testing framework built around the ammeter emulators in [`Ammeters/`](Ammeters/README.md) (Greenlee, ENTES, CIRCUTOR): it samples them, computes statistics, archives results, plots measurements, and compares ammeters against each other. For what each emulator does, its port/command, and its physics formula, see [`Ammeters/README.md`](Ammeters/README.md). For the bugs found and fixed and the reasoning behind every design decision, see [`DESIGN.md`](DESIGN.md). For the test strategy, see [`TestPlan.md`](TestPlan.md).

## Project Structure

- `Ammeters/` — the ammeter emulators and client (see [`Ammeters/README.md`](Ammeters/README.md)).
- `config/config.yaml` — config-driven settings for the testing framework (ammeters, sampling, analysis, result management).
- `src/`
  - `testing/`
    - `test_framework.py` — `AmmeterTestFramework`, the unified measurement API (`run_test_session(ammeter_type) -> TestResult`).
    - `statistics_analyzer.py` — mean/median/stdev/min/max, cross-ammeter comparison, confidence intervals.
    - `result_manager.py` — JSON-file result archiving (save/load/list/compare by run ID).
    - `visualization.py` — per-run line + histogram plots.
  - `utils/`
    - `config.py`, `logger.py`, `Utils.py`, `emulator_launcher.py` (shared emulator-thread startup).
- `run_test_suite.py` — config-driven CLI, the main way to exercise the full framework.
- `examples/run_tests.py` — not in use.
- `tests/` — pytest suite verifying the ammeter emulator system (see [`TestPlan.md`](TestPlan.md)).
- `main.py` — starts all three emulators and requests one measurement from each; the quickest smoke test.

## Setup

```sh
python -m venv .venv
.venv\Scripts\activate        # Windows (cmd/PowerShell)
source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Installed libraries: `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pandas` (all pre-declared), plus `pytest` (added for the test suite). See [`DESIGN.md`](DESIGN.md) for why each is used.

## Running things

**Smoke test** — start all three emulators and request one measurement from each:
```sh
python main.py
```

**Full framework run** (config-driven: samples N times per ammeter, computes stats, archives results, saves plots, optionally compares ammeters):
```sh
python run_test_suite.py --ammeter all --compare
```
Options: `--ammeter {greenlee,entes,circutor,all}`, `--config <path>` (defaults to `config/config.yaml`), `--no-plot`, `--compare`, `--history`.

**Retrieving and comparing past results** (no new sampling, reads from `results/`):
```sh
python run_test_suite.py --history --ammeter greenlee          # list all archived greenlee runs
python run_test_suite.py --history --ammeter all --compare     # compare the latest archived run per ammeter
```

**Running tests**:
```sh
python -m pytest tests/ --junitxml=results/pytest_reports/junit.xml -v
python -m pytest tests/ -m unit          # fast subset, no live sockets
python -m pytest tests/ -m integration   # live-socket tests only
```

## Sample results

Committed under `results/`: three archived measurement runs (one per ammeter, `results/<run_id>.json`) with matching plots (`results/plots/*.png`), a cross-ammeter comparison (`results/comparisons/<timestamp>.json` — stats, coefficient of variation, and 95% confidence intervals per ammeter) from the same `run_test_suite.py --ammeter all --compare` run, and a pytest run report (`results/pytest_reports/junit.xml` + a `pytest_sessionfinish`-hook-generated summary JSON) proving the test suite passes.
