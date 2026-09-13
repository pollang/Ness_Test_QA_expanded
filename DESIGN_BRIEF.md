# Design Decisions — Brief

(Full detail and reasoning: `DESIGN.md`. This is the short version.)

## Bugs found and fixed

1. **`main.py`** — client sent short command strings that didn't match the server's exact-byte check. Fixed by sending `ammeter.get_current_command` directly instead of a duplicated string.
2. **`Greenlee_Ammeter.py` / `base_ammeter.py`** — a `print()` with the Ω character crashed with `UnicodeEncodeError` when stdout wasn't UTF-8 (e.g. piped output). Since `base_ammeter.py` had no error handling around each connection, this crash permanently killed the emulator's server thread. Fixed by removing the Ω character and adding a `try/except` around connection handling.
3. **`test_framework.py`** — `Dict` was used in a type hint without being imported, causing a `NameError` on load. Fixed the import and implemented `run_test()`.
4. **`logger.py`** — a log file path was built but no handler was attached, so nothing was ever logged. Fixed by attaching `FileHandler` + `StreamHandler`.
5. **`examples/run_tests.py`** — called `run_test()` with a missing required argument. Fixed and updated to match the framework's API.

## Documentation fixes

- CIRCUTOR's real command includes a `-current` suffix the README didn't show. Fixed the doc, not the emulator.
- The README listed ports 5000/5001/5002; the code actually uses 5001/5002/5003. Fixed the doc to match the code.
- README split into two files: `Ammeters/README.md` (emulator reference, corrected values) and `README.md` (setup + usage instructions).

## Libraries used (all already in `requirements.txt`)

- `numpy` — mean/median/stdev/min/max.
- `pandas` — cross-ammeter comparison table.
- `scipy.stats` — confidence interval on the mean.
- `matplotlib` + `seaborn` — plots.
- `pyyaml` — config loading (already working, unchanged).
- `pytest` — added for the test suite.

## How results are stored

One JSON file per test run under `results/<run_id>.json`. No database needed for this scale.

`run_id` is named `<ammeter>_<date>_<time>_<milliseconds>` (e.g. `greenlee_20260913_202017_814`), not a random UUID, so a directory listing sorts by ammeter and then by time — you can actually tell what a file is and find the latest one without opening it.

Trade-off: unlike a UUID, this isn't guaranteed unique (two runs in the same millisecond would clash). Guarded two ways: `ensure_unique_run_id()` appends `_2`, `_3`, ... before a colliding id is ever used, and `save_result()` refuses to overwrite an existing file as a backstop. In practice a collision can't happen here since each run takes multiple seconds, but it's guarded instead of assumed away.

## Sampling

Samples are scheduled with `time.monotonic()` so timing doesn't drift over a long run. A failed sample is counted and skipped, not fatal to the whole run. Each sample opens a new TCP connection — the emulator's server closes the connection after every single request by design, so there's no persistent-connection option to use instead.

Scheduling samples carefully doesn't guarantee they land on time — the connection/send/receive itself takes a small, variable amount of time. So each result also records `timing.actual_offsets_seconds` (when each sample actually happened) and `timing.max_jitter_seconds` (the worst-case deviation from its scheduled time), so "precise timing" is something you can check in the saved results, not just something assumed. The saved plot's x-axis uses the real elapsed time too.

## One registry for ammeter types

The three ammeter names used to be hardcoded in five separate places (CLI choices, the emulator launcher, and three test files). Adding a fourth ammeter type would have meant editing all five. Fixed by making `emulator_launcher.AMMETER_CLASSES` the one canonical list everything else derives from.

## Emulators run continuously

All three emulators start once, in background threads, for the whole process — they can't be cleanly stopped/restarted, so tests and the CLI just connect to whichever port they need.

## Framework vs. tests

`AmmeterTestFramework` is a plain class, callable the same way from the CLI, the example script, or a test. The pytest suite calls into it; it isn't built on top of pytest.

## `tests/conftest.py`

- `running_emulators` fixture: starts all three emulators once per test session, on separate test-only ports (15001-15003), so real tests and a manual `main.py` run never collide.
- `test_config_path` fixture: writes a throwaway config file (fast sampling, results go to a temp folder), so tests never touch the real `config/config.yaml` or `results/`.
- `pytest_sessionfinish` hook: writes a JSON summary of the test run to `results/pytest_reports/` after the whole suite finishes — pairs with `--junitxml` as the pytest "sample test results."

## Why `@pytest.mark.parametrize`

The same test is written once and run for all three ammeter types, instead of copy-pasting it three times. Each case is still reported separately if it fails, and adding a fourth ammeter type later would need no new test code.

## Accuracy Assessment bonus

The spec asks to compare ammeters and find the "most reliable"/"most accurate" one. There's no reference current to check against, so true accuracy can't be measured here — only precision (how consistent repeated readings are) can. `StatisticsAnalyzer.compare()` ranks ammeters by coefficient of variation (lower = more precise/consistent) and reports a 95% confidence interval per ammeter. `run_test_suite.py --compare` prints this (with a note that it's measuring precision, not accuracy) and saves it to `results/comparisons/<timestamp>.json`.

CV (not the confidence interval) is what actually drives the ranking — CI width shrinks just from taking more samples, independent of whether an ammeter is genuinely more consistent, so it would be misleading to rank by it if sample counts ever differed between ammeters. CI is shown as supporting detail per ammeter, not used to decide the ranking.

## "Performance consistency evaluation" bonus

Different from Accuracy Assessment above — this one is about *one* ammeter's own run, not comparing ammeters against each other. Before this, coefficient of variation only existed inside the cross-ammeter comparison, so a plain single-ammeter run had no consistency number of its own. Added `coefficient_of_variation` as a real metric in `StatisticsAnalyzer` and to the default config, so every run (live or historical) reports its own consistency automatically.

## Retrieving and comparing historical results (`--history`)

`ResultManager.list_results()` already read archived results off disk, but was never wired into anything runnable. Added `run_test_suite.py --history`: `--history --ammeter <type>` lists every past run for that ammeter (with mean/median/stdev/CV per run); `--history --ammeter all --compare` takes the latest archived run per ammeter and runs them through the same `StatisticsAnalyzer.compare()` used for live results, so historical and live comparisons look identical and both get saved under `results/comparisons/`.

## Cross-platform notes

- Verified on Windows only.
- The Ω bug: confirmed to reproduce only when stdout is piped (not in a native console) — fixed regardless, since CI and IDE runners commonly pipe output.
- `matplotlib.use("Agg")` avoids needing a display, which matters on headless Linux.
- Log file writing is pinned to UTF-8 explicitly, to avoid the same class of encoding issue.
- `pathlib.Path` used for all result/plot file paths instead of hand-built strings.

## Code quality cleanup

Cleaned up during a code-quality pass: the CV metric's dense one-line lambda became a small named function; `_collect_samples()`'s bare 4-tuple return became a `NamedTuple` (self-documenting, same unpacking still works); Hebrew comments in `logger.py`/`config.py` translated to English; an unused `import datetime` removed from `base_ammeter.py`.

## Environment

Python 3.12.5, project-local `.venv` — matches the original project's own PyCharm config (`.idea/misc.xml` pins Python 3.12).
