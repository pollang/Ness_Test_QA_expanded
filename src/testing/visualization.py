from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # headless, cross-platform backend - no GUI/Tk dependency
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme()


def plot_measurement_run(
    readings: List[float],
    ammeter_type: str,
    run_id: str,
    sample_timestamps: Optional[List[float]] = None,
    plots_dir: str = "results/plots",
) -> str:
    """Saves a line plot (current vs. actual elapsed time) and a histogram for one
    test run to a single PNG, returning the saved file path. `sample_timestamps`
    are each sample's actual time offset (seconds) from the run's start, as
    recorded by AmmeterTestFramework.run_test_session - falls back to sample index if
    not provided."""
    Path(plots_dir).mkdir(parents=True, exist_ok=True)
    fig, (ax_line, ax_hist) = plt.subplots(1, 2, figsize=(10, 4))

    if sample_timestamps:
        ax_line.plot(sample_timestamps, readings, marker="o")
        ax_line.set_xlabel("Elapsed time (s)")
    else:
        ax_line.plot(range(1, len(readings) + 1), readings, marker="o")
        ax_line.set_xlabel("Sample #")
    ax_line.set_title(f"{ammeter_type} - current over time")
    ax_line.set_ylabel("Current (A)")

    sns.histplot(readings, ax=ax_hist, kde=True)
    ax_hist.set_title(f"{ammeter_type} - reading distribution")
    ax_hist.set_xlabel("Current (A)")

    fig.suptitle(f"Run {run_id}")
    fig.tight_layout()

    # run_id already embeds the ammeter type (see AmmeterTestFramework.run_test_session), so
    # the filename doesn't need to repeat it.
    path = Path(plots_dir) / f"{run_id}.png"
    fig.savefig(path)
    plt.close(fig)
    return str(path)
