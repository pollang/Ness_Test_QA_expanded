from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


class StatisticsAnalyzer:
    """Computes statistical metrics on ammeter current readings and compares ammeters."""

    _METRIC_FUNCS = {
        "mean": lambda d: float(np.mean(d)),
        "median": lambda d: float(np.median(d)),
        "stdev": lambda d: float(np.std(d, ddof=1)) if len(d) > 1 else 0.0,
        "min": lambda d: float(np.min(d)),
        "max": lambda d: float(np.max(d)),
    }

    @classmethod
    def compute(cls, readings: List[float], metrics: List[str]) -> Dict[str, Optional[float]]:
        if not readings:
            return {metric: None for metric in metrics}
        return {metric: cls._METRIC_FUNCS[metric](readings) for metric in metrics if metric in cls._METRIC_FUNCS}

    @staticmethod
    def confidence_interval(readings: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """95%-style t-distribution confidence interval on the mean, as a (low, high) tuple."""
        if len(readings) < 2:
            value = float(readings[0]) if readings else 0.0
            return (value, value)
        mean = float(np.mean(readings))
        sem = scipy_stats.sem(readings)
        margin = sem * scipy_stats.t.ppf((1 + confidence) / 2, len(readings) - 1)
        return (mean - margin, mean + margin)

    @classmethod
    def compare(cls, results_by_ammeter: Dict[str, Dict]) -> pd.DataFrame:
        """
        Builds a comparison table across ammeter types.
        `results_by_ammeter` maps ammeter_type -> result dict (as produced by
        AmmeterTestFramework.run_test), each containing a "raw_readings" list.

        Returns a DataFrame indexed by ammeter_type, sorted by coefficient of
        variation (stdev/mean) ascending - i.e. by measurement PRECISION
        (how tightly repeated readings cluster together), not accuracy.
        There is no reference/calibrated current here to compare against, so
        true accuracy (closeness to a known-correct value) cannot be computed -
        only precision/consistency can. The lowest-CV ammeter is the most
        precise (most consistent), not necessarily the most "accurate".
        """
        rows = []
        for ammeter_type, result in results_by_ammeter.items():
            readings = result.get("raw_readings", [])
            stats_dict = cls.compute(readings, ["mean", "median", "stdev", "min", "max"])
            mean = stats_dict["mean"] or 0.0
            stdev = stats_dict["stdev"] or 0.0
            cv = (stdev / mean) if mean else float("inf")
            ci_low, ci_high = cls.confidence_interval(readings)
            rows.append({
                "ammeter_type": ammeter_type,
                "mean": mean,
                "median": stats_dict["median"],
                "stdev": stdev,
                "min": stats_dict["min"],
                "max": stats_dict["max"],
                "coefficient_of_variation": cv,
                "ci_95_low": ci_low,
                "ci_95_high": ci_high,
            })
        df = pd.DataFrame(rows).set_index("ammeter_type")
        return df.sort_values("coefficient_of_variation")
