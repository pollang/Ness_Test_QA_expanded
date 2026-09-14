# Design Decisions — Brief

## Bugs found and fixed

1. `main.py` — client sent short command strings that didn't match the server's exact-byte check. Fixed by sending `ammeter.get_current_command` directly.
2. `Greenlee_Ammeter.py` / `base_ammeter.py` — a `print()` with Ω crashed under non-UTF-8 stdout (e.g. piped output), and with no error handling around each connection, that crash permanently killed the emulator's server thread. Fixed: removed Ω from the print, added a `try/except` around connection handling.
3. `test_framework.py` — `Dict` used in a type hint without being imported, causing `NameError` on load. Fixed the import, implemented `run_test_session()`.
4. `logger.py` — a log path was built but no handler attached, so nothing was ever logged. Fixed by attaching `FileHandler` + `StreamHandler`.
5. `examples/run_tests.py` — called `run_test()` with a missing argument. Fixed, marked `# not in use` (matches the original repo's own stance); `run_test_suite.py` is the real entry point.

## Documentation fixes

- CIRCUTOR's real command has a `-current` suffix the README didn't show — fixed the doc.
- README listed ports 5000/5001/5002; code uses 5001/5002/5003 — fixed the doc.
- Split into `AMMETERS_README.md` (emulator reference) and `README.md` (setup + usage).

## Libraries used (all already in `requirements.txt`)

`numpy` (statistics), `pandas` (comparison table), `scipy.stats` (confidence interval), `matplotlib` + `seaborn` (plots), `pyyaml` (config, unchanged). `pytest` is the one addition, for the test suite.

## How results are stored

One JSON file per run, `results/<run_id>.json` — no database needed at this scale. `run_id` is `<ammeter>_<date>_<time>_<ms>` (sortable by ammeter, then time), not a UUID, so it isn't collision-proof — guarded by `ensure_unique_run_id()` plus a refuse-to-overwrite check in `save_result()`.

## Sampling

Scheduled with `time.monotonic()` so timing doesn't drift over a run. A failed sample is counted and skipped, not fatal. Each result also records actual sample offsets and max jitter, so "precise timing" is checkable in the data, not just assumed.

## Considered and rejected: capturing each emulator's raw physics inputs

Each emulator's random inputs (voltage/resistance, etc.) are printed to console and lost — not a bug, so exposing them is out of scope under the spec's "fix only real errors" constraint. Also not reachable: the framework only ever talks over the TCP socket, never holds the emulator object.

## One registry for ammeter types

The three ammeter names used to be hardcoded in five places. Fixed by making `emulator_launcher.AMMETER_CLASSES` the one canonical list everything else derives from.

## Emulators run continuously

All three start once, in background threads, for the whole process — `start_server()` has no clean shutdown, so tests and the CLI just connect to whichever port they need.

## Framework vs. tests

`AmmeterTestFramework` is a plain class, callable the same way from the CLI, the example script, or a test — not built on pytest.

## `tests/conftest.py`

- `running_emulators` — starts all three emulators once per session, on test-only ports (15001-15003).
- `test_config_path` — loads `config/test_config.yaml`, injects `TEST_AMMETERS`, points results at a temp folder.
- `pytest_sessionfinish` hook — writes a JSON run summary to `results/pytest_reports/`.

## Why `@pytest.mark.parametrize`

One test body runs for all three ammeter types instead of three copies; each case is still reported individually on failure. `test_test_framework.py` also doubles as a usage example — it calls `run_test_session()` the same way any real caller would.

## Accuracy Assessment bonus

No reference current exists, so true accuracy can't be measured — only precision (consistency). `StatisticsAnalyzer.compare()` ranks ammeters by coefficient of variation (lower = more precise); a 95% confidence interval is shown as supporting detail, not what drives the ranking.

## "Performance consistency evaluation" bonus

Distinct from Accuracy Assessment above — this is one ammeter's own run, not a cross-ammeter comparison. Added `coefficient_of_variation` as a real per-run metric, so every run reports its own consistency automatically.

## Error simulation bonus

`error_probability` is an explicit parameter on `run_test_session()` (`--simulate-errors PROBABILITY` on the CLI), not a `config.yaml` field — simulating a failure is a one-off choice for a specific invocation, not a standing property of the system, and keeping it out of config avoids a knob that could accidentally stay on in a committed config file. It also makes the feature directly testable: a caller can pass `error_probability=1.0` and deterministically assert on the result.

When triggered, it picks one of three real failure modes rather than always the same one: `refuse` (raises before any socket work), `timeout` (a real, very short socket timeout against the real connection), `corrupt` (the real request/response happens, then the real received bytes are corrupted before parsing). This exercises three of the four exception types `_collect_samples()` actually handles, instead of only one.

## Retrieving and comparing historical results (`--history`)

`ResultManager.list_results()` existed but was never wired to anything runnable. Added `run_test_suite.py --history`: lists archived runs, and can compare the latest run per ammeter using the same `compare()` used for live results.

## Cross-platform notes

- Verified on Windows only.
- The Ω bug only reproduces when stdout is piped — fixed regardless, since CI/IDE runners commonly pipe output.
- `matplotlib.use("Agg")` avoids needing a display.
- Log files are pinned to UTF-8.
- `pathlib.Path` used for all result/plot paths.

## Result: `Dict` → `TestResult` dataclass

The result dict had no enforced shape. Replaced with `TestResult`/`SamplingTiming` dataclasses (stdlib `dataclasses`, no new dependency). `to_dict()`/`from_dict()` handle the JSON boundary; everywhere else uses the dataclass directly.

## Error handling: plotting can't lose archived data anymore

Plotting used to run before saving, with no error handling — a plotting failure meant the run's data was never archived. Reordering alone doesn't work cleanly (missing `plot_path`, double-save conflict with the run_id guard). Fixed with a `try/except` around just the plotting call: the failure is logged and skipped, the result is still saved.

## Environment

Python 3.12.5, project-local `.venv` — matches the original project's PyCharm config.
