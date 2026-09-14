from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class SamplingTiming:
    actual_offsets_seconds: List[float]
    max_jitter_seconds: float


@dataclass
class TestResult:
    """One ammeter test run - what AmmeterTestFramework.run_test_session() returns,
    and what gets archived to/loaded from results/<run_id>.json."""
    run_id: str
    ammeter_type: str
    timestamp: str
    config_snapshot: Dict
    raw_readings: List[float]
    statistics: Dict[str, Optional[float]]
    samples_requested: int
    samples_collected: int
    errors: int
    timing: SamplingTiming
    plot_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "TestResult":
        data = dict(data)
        timing_data = data.pop("timing")
        return cls(timing=SamplingTiming(**timing_data), **data)
