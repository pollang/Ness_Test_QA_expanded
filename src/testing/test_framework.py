import random
import socket
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from src.testing.result_manager import ResultManager
from src.testing.statistics_analyzer import StatisticsAnalyzer
from src.utils.logger import TestLogger
from src.utils.config import load_config


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
        error_injection_cfg = self.config.get("testing", {}).get("error_injection", {}) or {}

        measurements_count = sampling_cfg["measurements_count"]
        total_duration = sampling_cfg["total_duration_seconds"]
        frequency = sampling_cfg["sampling_frequency_hz"]
        drop_probability = error_injection_cfg.get("drop_probability", 0)

        readings: List[float] = []
        errors = 0
        start_time = time.monotonic()

        self.logger.info(f"Starting test run for {ammeter_type}: "
                          f"{measurements_count} samples @ {frequency}Hz, max {total_duration}s")

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
            except (ConnectionRefusedError, ConnectionError, socket.timeout, ValueError) as exc:
                errors += 1
                self.logger.error(f"{ammeter_type}: sample {i} failed: {exc}")

        metrics = analysis_cfg.get("statistical_metrics") or ["mean", "median", "stdev", "min", "max"]
        statistics = StatisticsAnalyzer.compute(readings, metrics)

        run_id = str(uuid.uuid4())
        result = {
            "run_id": run_id,
            "ammeter_type": ammeter_type,
            "timestamp": datetime.now().isoformat(),
            "config_snapshot": {"ammeter": ammeter_cfg, "sampling": sampling_cfg},
            "raw_readings": readings,
            "statistics": statistics,
            "samples_requested": measurements_count,
            "samples_collected": len(readings),
            "errors": errors,
        }

        visualization_cfg = analysis_cfg.get("visualization", {}) or {}
        if visualization_cfg.get("enabled") and readings:
            from src.testing.visualization import plot_measurement_run
            result["plot_path"] = plot_measurement_run(readings, ammeter_type, run_id)

        self.result_manager.save_result(result)
        self.logger.info(f"{ammeter_type}: collected {len(readings)}/{measurements_count} samples, "
                          f"{errors} errors, run_id={run_id}")
        return result

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
