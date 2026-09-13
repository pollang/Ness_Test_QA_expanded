import random
import socket
import time
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional

from src.testing.result_manager import ResultManager
from src.testing.statistics_analyzer import StatisticsAnalyzer
from src.utils.logger import TestLogger
from src.utils.config import load_config


class SamplingOutcome(NamedTuple):
    readings: List[float]
    sample_timestamps: List[float]
    errors: int
    max_jitter_seconds: float


class AmmeterTestFramework:
    """
    Unified measurement API: the same run_test(ammeter_type) call works across
    all configured ammeter types (Greenlee, ENTES, CIRCUTOR) and always returns
    a result dict with the same shape, regardless of each ammeter's underlying
    protocol/port/physics.
    """

    def __init__(self, config_path: str = "config/config.yaml", results_dir: Optional[str] = None):
        self.config = load_config(config_path)
        result_management_cfg = self.config.get("result_management", {}) or {}
        self.result_manager = ResultManager(results_dir or result_management_cfg.get("results_dir", "results"))
        self.logger = TestLogger("ammeter_test_framework")

    def run_test(self, ammeter_type: str) -> Dict:
        ammeters_cfg = self.config["ammeters"]
        if ammeter_type not in ammeters_cfg:
            raise ValueError(f"Unknown ammeter_type '{ammeter_type}', expected one of {list(ammeters_cfg)}")

        ammeter_cfg = ammeters_cfg[ammeter_type]
        sampling_cfg = self.config["testing"]["sampling"]
        analysis_cfg = self.config.get("analysis", {}) or {}
        drop_probability = self.config.get("testing", {}).get("error_injection", {}).get("drop_probability", 0)

        self.logger.info(f"Starting test run for {ammeter_type}: "
                          f"{sampling_cfg['measurements_count']} samples @ {sampling_cfg['sampling_frequency_hz']}Hz, "
                          f"max {sampling_cfg['total_duration_seconds']}s")

        readings, sample_timestamps, errors, max_jitter_seconds = self._collect_samples(
            ammeter_type, ammeter_cfg, sampling_cfg, drop_probability
        )

        metrics = analysis_cfg.get("statistical_metrics") or ["mean", "median", "stdev", "min", "max"]
        statistics = StatisticsAnalyzer.compute(readings, metrics)

        # Human-readable, sortable id: <ammeter_type>_<YYYYMMDD>_<HHMMSS>_<milliseconds>
        # e.g. "greenlee_20260913_200306_123" - lexicographic sort groups by ammeter
        # and then puts the latest run last, which a random UUID couldn't do. Unlike a
        # UUID this isn't inherently collision-proof, so ensure_unique_run_id() checks
        # for (and resolves) a same-millisecond collision before it's ever used.
        run_id = self.result_manager.ensure_unique_run_id(
            f"{ammeter_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
        )
        result = {
            "run_id": run_id,
            "ammeter_type": ammeter_type,
            "timestamp": datetime.now().isoformat(),
            "config_snapshot": {"ammeter": ammeter_cfg, "sampling": sampling_cfg},
            "raw_readings": readings,
            "statistics": statistics,
            "samples_requested": sampling_cfg["measurements_count"],
            "samples_collected": len(readings),
            "errors": errors,
            "timing": {
                "actual_offsets_seconds": sample_timestamps,
                "max_jitter_seconds": max_jitter_seconds,
            },
        }

        visualization_cfg = analysis_cfg.get("visualization", {}) or {}
        if visualization_cfg.get("enabled") and readings:
            from src.testing.visualization import plot_measurement_run
            result["plot_path"] = plot_measurement_run(readings, ammeter_type, run_id, sample_timestamps)

        self.result_manager.save_result(result)
        self.logger.info(f"{ammeter_type}: collected {len(readings)}/{sampling_cfg['measurements_count']} samples, "
                          f"{errors} errors, run_id={run_id}")
        return result

    def _collect_samples(
        self, ammeter_type: str, ammeter_cfg: Dict, sampling_cfg: Dict, drop_probability: float
    ) -> SamplingOutcome:
        """Runs the timed sampling loop against one ammeter.
        See run_test()'s "timing" docs for what jitter means."""
        measurements_count = sampling_cfg["measurements_count"]
        total_duration = sampling_cfg["total_duration_seconds"]
        frequency = sampling_cfg["sampling_frequency_hz"]

        readings: List[float] = []
        sample_timestamps: List[float] = []
        errors = 0
        max_jitter_seconds = 0.0
        start_time = time.monotonic()

        for i in range(measurements_count):
            if time.monotonic() - start_time >= total_duration:
                self.logger.warning(f"{ammeter_type}: stopping early, total_duration_seconds elapsed")
                break

            target_time = start_time + i / frequency
            sleep_for = target_time - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

            try:
                reading = self._sample_once(ammeter_cfg["port"], ammeter_cfg["command"], drop_probability)
                readings.append(reading)
                actual_offset = time.monotonic() - start_time
                sample_timestamps.append(actual_offset)
                # Jitter = how far this sample landed from its scheduled target_time - what
                # makes "precise timing" a checkable claim instead of an assumption, since the
                # scheduling loop only controls when a sample is *attempted*, not how long the
                # TCP connect/send/recv to the emulator actually takes.
                max_jitter_seconds = max(max_jitter_seconds, abs(actual_offset - (target_time - start_time)))
            except (ConnectionRefusedError, ConnectionError, socket.timeout, ValueError) as exc:
                errors += 1
                self.logger.error(f"{ammeter_type}: sample {i} failed: {exc}")

        return SamplingOutcome(readings, sample_timestamps, errors, max_jitter_seconds)

    @staticmethod
    def _sample_once(port: int, command: str, drop_probability: float = 0.0, timeout: float = 2.0) -> float:
        if drop_probability and random.random() < drop_probability:
            raise ConnectionError("Simulated dropped reading (error_injection)")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(("localhost", port))
            s.sendall(command.encode("utf-8"))
            data = s.recv(1024)
            if not data:
                raise ConnectionError("No data received from ammeter")
            return float(data.decode("utf-8"))
