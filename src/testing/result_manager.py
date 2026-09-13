import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ResultManager:
    """Archives ammeter test-run results as one JSON file per run under results_dir."""

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.comparisons_dir = self.results_dir / "comparisons"

    def save_result(self, result: Dict) -> str:
        run_id = result["run_id"]
        path = self.results_dir / f"{run_id}.json"
        if path.exists():
            # run_id is timestamp-based, not a UUID, so it isn't collision-proof
            raise FileExistsError(f"A result already exists at {path} - refusing to overwrite it (run_id collision)")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return run_id

    def ensure_unique_run_id(self, run_id: str) -> str:
        """Returns run_id unchanged if results_dir/<run_id>.json doesn't exist yet,
        otherwise appends _2, _3, ... until it finds one that doesn't."""
        if not (self.results_dir / f"{run_id}.json").exists():
            return run_id
        suffix = 2
        while (self.results_dir / f"{run_id}_{suffix}.json").exists():
            suffix += 1
        return f"{run_id}_{suffix}"

    def load_result(self, run_id: str) -> Dict:
        path = self.results_dir / f"{run_id}.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_results(self, ammeter_type: Optional[str] = None) -> List[Dict]:
        results = []
        for path in sorted(self.results_dir.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                result = json.load(f)
            if ammeter_type is None or result.get("ammeter_type") == ammeter_type:
                results.append(result)
        return results

    def save_comparison(self, comparison: Dict) -> str:
        """Saves a cross-ammeter comparison (see StatisticsAnalyzer.compare) under
        results/comparisons/, separate from per-run files so it's never picked up
        by list_results()'s top-level glob. Returns the saved file path."""
        self.comparisons_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        path = self.comparisons_dir / f"comparison_{timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)
        return str(path)
