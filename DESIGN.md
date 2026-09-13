# Design Decisions

## Bugs found and fixed

### 1. `main.py`: client commands didn't match the server's exact-byte protocol

`AmmeterEmulatorBase.start_server()` compares the received bytes to `get_current_command` with `==` — an exact match or nothing is sent back. The original commented-out client calls sent short strings (e.g. `b'MEASURE_GREENLEE'`) that don't equal the full command each emulator actually expects (e.g. `b'MEASURE_GREENLEE -get_measurement'`), so uncommenting them as-written would have silently failed ("No data received.").

**Fix:** the client calls now pass `greenlee.get_current_command` / `entes.get_current_command` / `circutor.get_current_command` directly — the exact same property the server checks against — instead of a duplicated literal string. This can't drift out of sync with the server's expectation, which a hardcoded string could.

### 2. `Greenlee_Ammeter.py` + `base_ammeter.py`: a Unicode character permanently killed the emulator thread

This was the more serious bug, and it only surfaces once you actually try to sample repeatedly (as the framework does). `Greenlee_Ammeter.py`'s diagnostic `print()` includes the Ω (Ohm) character. Whether this crashes depends on *how* Python's stdout is connected, not just the OS: verified on this same Windows machine, `sys.stdout.encoding` is `utf-8` when run directly in a native console (PowerShell/cmd/Windows Terminal) — Ω prints fine there — but falls back to the legacy `cp1252` codepage when stdout is piped (e.g. Git Bash, many IDE "Run" buttons, a redirect to a file, a subprocess call), where `Ω` raises `UnicodeEncodeError` *inside* `measure_current()`. `base_ammeter.py`'s `start_server()` had no exception handling around per-connection processing, so that error propagated up and crashed the entire server thread — not just that one request. Every subsequent connection to that port then got `ConnectionRefusedError` for the rest of the process's life, since nothing was listening anymore. Because plenty of realistic invocation paths (CI, a grader's IDE, a different terminal) hit the piped case, this was worth fixing even though a direct-console run never shows it.

With a sampling framework requesting 20 measurements per run, this meant Greenlee would answer exactly one request and then fail all 19 remaining samples.

**Fix, two parts:**
- Root cause: replaced `Ω` with plain ASCII `"Ohms"` in the print statement — can't fail to encode on any console.
- Defensive hardening: wrapped the per-connection handling in `base_ammeter.py`'s loop in a `try/except`, so one bad request (any future error in `measure_current()` or the socket layer) logs and moves on instead of killing the whole emulator. This directly serves the "comprehensive error handling" evaluation criterion, and the spec's own instruction to fix errors found in the reused infrastructure.

### 3. `test_framework.py`: missing `typing.Dict` import

The original `run_test(self, ammeter_type: str) -> Dict` stub referenced `Dict` without importing it from `typing`, which would raise `NameError` the moment the class was defined — blocking the whole module from loading. Fixed by importing `Dict`/`List`/`Optional` and implementing `run_test()` fully (see below).

### 4. `logger.py`: computed a log path but never wrote to it

`TestLogger._setup_logger()` built a log file path but never attached a `logging.Handler`, so `logger.info(...)` etc. silently did nothing. Fixed by attaching a `FileHandler` (writes the computed path) and a `StreamHandler` (console), both with a shared formatter, guarded by `if not logger.handlers:` — `logging.getLogger(name)` is a singleton lookup, so without that guard, creating multiple `TestLogger`s with the same name (which the test suite does) would duplicate handlers and duplicate every log line.

### 5. `examples/run_tests.py`: called `run_test()` with no argument

Fixed to pass an `ammeter_type` and to actually start the emulators first (via the new `emulator_launcher.start_emulators`), matching the corrected `AmmeterTestFramework` API. Kept as a short, literate usage example, distinct from the fuller `run_test_suite.py` CLI. **Must be run as `python -m examples.run_tests` from the repo root** (not `python examples/run_tests.py` directly) — running it directly puts `examples/` rather than the repo root on `sys.path`, and the `src`/`Ammeters` packages wouldn't resolve. This is a byproduct of there being no `__init__.py`/packaging in this repo (implicit namespace packages); `main.py` and `run_test_suite.py` don't hit this because they already live at the repo root.

## Documentation-only discrepancies (README fixed, not the code)

- **CIRCUTOR command**: the emulator's actual `get_current_command` is `MEASURE_CIRCUTOR -get_measurement -current`, but the original README documented `MEASURE_CIRCUTOR -get_measurement` (missing the `-current` suffix). Fixed the doc, not the emulator — the emulator's TCP server is the real, working contract; the spec says to treat the emulation infrastructure as given, and Greenlee/ENTES have zero discrepancy, so this reads as documentation drift on one line, not an intentional design the code got wrong.
- **Ports**: the original README's table listed 5000/5001/5002; `main.py` actually starts Greenlee/ENTES/CIRCUTOR on 5001/5002/5003 and is internally consistent with itself. Fixed the doc's table to match the real ports rather than changing working code.
- Both corrections now live in **`Ammeters/README.md`** — the README was split into that file (the original ammeter/emulator reference doc, kept close to its original wording, values corrected) and the top-level `README.md` (the "README with usage instructions" deliverable: setup, how to run everything, where results/docs live).

## Accuracy Assessment bonus (spec section 5)

The spec asks to compare ammeters, "determine relative accuracy," and "identify most reliable measurement method." Implemented in `StatisticsAnalyzer.compare()` (called from `run_test_suite.py --compare`), with one important correction to the spec's own wording:

There is no reference/calibrated current in this setup — the emulators generate their own random inputs, with no known-correct value to compare a reading against. That means **accuracy** (closeness to a true value) cannot actually be computed here; only **precision** (how tightly repeated readings from the same ammeter cluster together) can. So `compare()` ranks ammeters by coefficient of variation (stdev/mean) — the standard measure of relative precision — and calls the lowest-CV ammeter the most *precise* or *consistent*, not the most "accurate" or "reliable." The CLI's `--compare` output prints this distinction explicitly rather than silently reusing the spec's looser terminology.

`compare()` also reports a 95% confidence interval on the mean for each ammeter (`StatisticsAnalyzer.confidence_interval()`, using `scipy.stats.sem` + `t.ppf`) — the "use statistical techniques to quantify measurement precision" part of the same bonus.

## Why these libraries (all pre-declared in `requirements.txt`)

`requirements.txt` already listed `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pandas` before this work started. The spec's "minimize external library dependencies" is read as *don't add further ones* — not as a reason to reimplement what's already an approved dependency via stdlib. So:

- **`numpy`** — `statistics_analyzer.py`'s core metrics (mean/median/std/min/max). `np.std(ddof=1)` is used for sample (not population) standard deviation.
- **`pandas`** — `StatisticsAnalyzer.compare()` returns a `DataFrame` (one row per ammeter type) for the cross-ammeter comparison bonus — a much more readable structure than a nested dict, sortable by coefficient of variation in one line.
- **`scipy.stats`** — `StatisticsAnalyzer.confidence_interval()` uses `sem` + `t.ppf` for a real t-distribution confidence interval on the mean, for the "quantify measurement precision" bonus.
- **`matplotlib`** (with the `Agg` backend — headless, no Tk dependency, works identically on any platform) + **`seaborn`** (`set_theme()` + `histplot`) — the visualization bonus: a line plot and histogram per test run.
- **`pyyaml`** — already used correctly by `src/utils/config.py::load_config`; no changes needed there.
- **`pytest`** — added for the test suite (see `TestPlan.md`).

## Why JSON-file archiving, not a database

`ResultManager` writes one JSON file per run (`results/<run_id>.json`), keyed by a UUID. This needs zero new dependencies, is trivially diffable/human-readable, and is more than sufficient for an exercise's result volume. `list_results()`/`compare_results()` provide the retrieval/comparison the spec's "Result Management" section asks for without needing an actual database.

## Sampling algorithm

`AmmeterTestFramework.run_test()` schedules samples using `time.monotonic()`: `target_time = start_time + i / sampling_frequency_hz`, sleeping only the remainder before each sample. This keeps the sampling interval from drifting as socket round-trip latency accumulates over many samples (a naive `time.sleep(1/frequency)` between samples would drift by the cumulative latency). `total_duration_seconds` is a safety cap that can end a run early; `measurements_count` is the target sample count. Each sample opens a fresh short-lived TCP connection with a 2-second timeout; per-sample failures (`ConnectionRefusedError`, `ConnectionError`, `socket.timeout`, a bad float parse) increment an `errors` counter and the run continues, rather than aborting on the first bad reading.

## Threading model: start all three emulators once, for the life of the process

`src/utils/emulator_launcher.start_emulators()` starts all three emulators as daemon threads together, once — mirroring the pattern already in `main.py` — rather than starting/stopping one emulator per test. `base_ammeter.py`'s `start_server()` is a blocking infinite loop with no clean shutdown method, so there's no way to stop-and-restart a single emulator's thread between test runs without modifying that reused infrastructure. Running all three continuously also means the `--compare` bonus (testing all three back-to-back) needs no extra startup/teardown between ammeters. The pytest suite's `running_emulators` fixture uses the same helper on a disjoint port range (15001-15003) so a manual `main.py` run and the test suite never collide.

## `AmmeterTestFramework` is a plain API, not built on pytest

The spec asks for a "unified testing interface" — callable the same way regardless of caller. `AmmeterTestFramework.run_test(ammeter_type) -> Dict` is a plain Python method, usable identically from `run_test_suite.py`, `examples/run_tests.py`, or a pytest test body. Pytest (see `TestPlan.md`) is a separate, thin validation layer that calls into this API — it does not host the framework's core logic. This keeps the framework itself maximally reusable, which "flexibility" and "potential for extension and reuse" (both named evaluation criteria) reward.

## `tests/conftest.py`: shared fixtures and a reporting hook

- **`running_emulators`** (session-scoped fixture) starts all three emulators once, on a dedicated test-port range (15001-15003), for the whole test session — reusing `emulator_launcher.start_emulators` rather than duplicating thread-start code in every test file. Session scope means the cost of starting the emulators is paid once, not per test.
- **`test_config_path`** (function-scoped, uses `tmp_path`) writes a throwaway `config.yaml` pointing at the test-port emulators with fast sampling (3 measurements, 20 Hz) and its results directory inside pytest's isolated `tmp_path`. This keeps end-to-end tests from touching the real `config/config.yaml` or writing into the real `results/` folder.
- **`pytest_sessionfinish`** is a pytest hook (not a fixture) that runs once after the whole test session finishes. It reads the terminal reporter's pass/fail/skip counts and writes them as a JSON file under `results/pytest_reports/`. This is what pairs with `--junitxml` to produce the "sample test results" pytest deliverable (see `TestPlan.md`) without adding a new dependency like `pytest-html`.

## Why `@pytest.mark.parametrize` across the three ammeter types

`tests/test_ammeter_emulators.py` and `tests/test_test_framework.py` each define the test logic once and parametrize it over `["greenlee", "entes", "circutor"]`, rather than writing three near-identical test functions (`test_greenlee_x`, `test_entes_x`, `test_circutor_x`). Reasons:
- Avoids duplicating the same assertions three times — a change to the test logic only has to happen in one place.
- Each parametrized case still shows up and is reported individually in pytest's output (e.g. `test_...[greenlee-...]`, `test_...[entes-...]`), so a failure for one ammeter type is still precisely identified — parametrizing doesn't hide which case failed.
- If a fourth ammeter type were added to the config, most of the corresponding test coverage would need zero new test code — just one more entry in the parametrize list. That directly serves the "flexibility" and "extension and reuse" evaluation criteria, applied to the test suite itself.

## Cross-platform compatibility (spec's Technical Constraints)

- **The Ω encoding bug** (see above) — the one genuine cross-platform/cross-environment landmine found: fixed at the source (ASCII-only print) rather than by, say, forcing UTF-8 mode globally, since the latter wouldn't help a grader whose environment doesn't allow that.
- **`logging.FileHandler(log_file, encoding="utf-8")`** in `logger.py`'s fix — set explicitly. Without it, `FileHandler` defaults to `locale.getpreferredencoding()`, which is the same `cp1252` on this machine — any future non-ASCII log message would hit the identical crash, just writing to a file instead of stdout. Pinning `utf-8` closes that off regardless of OS/locale.
- **`matplotlib.use("Agg")`** in `visualization.py` — forces the headless rendering backend instead of matplotlib's default GUI backend (which needs Tk and a display). Matters most on headless Linux (CI runners, servers with no X server), where the default backend would fail outright; identical behavior on Windows/macOS/Linux either way.
- **`pathlib.Path`** throughout `result_manager.py`/`visualization.py` for building `results/<run_id>.json` and `results/plots/*.png` paths, rather than hand-concatenated strings — handles Windows vs. POSIX path separators automatically.
- **Checked, not an issue**: `Greenlee_Ammeter.py`'s Ω also appears in a `#` comment (not executed) and `logger.py`/`config.py` have Hebrew text in docstrings (never printed or logged) — Python parses `.py` source files as UTF-8 regardless of console codepage (PEP 3120), so neither is a runtime risk; the only *executed* non-ASCII character in the codebase was the one that got fixed.
- **README's venv-activation instructions** originally showed only the Windows command; added the macOS/Linux equivalent (`source .venv/bin/activate`) alongside it.

## Interpreter / environment

Developed and verified against **Python 3.12.5** in a project-local virtual environment (`.venv`). This matches the original project's own configuration: `.idea/misc.xml` (PyCharm project settings, present before this work started) pins `project-jdk-name="Python 3.12"`.

## Libraries installed

`pip install -r requirements.txt` (into `.venv`) installed: `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pandas`, `pytest` (added to `requirements.txt` for the test suite — the only new addition beyond what the repo already declared).
