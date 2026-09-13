from pathlib import Path
from typing import List

import matplotlib
matplotlib.use("Agg")  # headless, cross-platform backend - no GUI/Tk dependency
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme()


def plot_measurement_run(readings: List[float], ammeter_type: str, run_id: str, plots_dir: str = "results/plots") -> str:
    """Saves a line plot (current vs. sample index) and a histogram for one test run
    to a single PNG, returning the saved file path."""
    Path(plots_dir).mkdir(parents=True, exist_ok=True)
    fig, (ax_line, ax_hist) = plt.subplots(1, 2, figsize=(10, 4))

    ax_line.plot(range(1, len(readings) + 1), readings, marker="o")
    ax_line.set_title(f"{ammeter_type} - current per sample")
    ax_line.set_xlabel("Sample #")
    ax_line.set_ylabel("Current (A)")

    sns.histplot(readings, ax=ax_hist, kde=True)
    ax_hist.set_title(f"{ammeter_type} - reading distribution")
    ax_hist.set_xlabel("Current (A)")

    fig.suptitle(f"Run {run_id}")
    fig.tight_layout()

    path = Path(plots_dir) / f"{run_id}_{ammeter_type}.png"
    fig.savefig(path)
    plt.close(fig)
    return str(path)
