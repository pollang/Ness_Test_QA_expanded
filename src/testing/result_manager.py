import json
from pathlib import Path
from typing import Dict, List, Optional


class ResultManager:
    """Archives ammeter test-run results as one JSON file per run under results_dir."""

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: Dict) -> str:
        run_id = result["run_id"]
        path = self.results_dir / f"{run_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return run_id

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

    def compare_results(self, run_ids: List[str]) -> Dict[str, Dict]:
        return {run_id: self.load_result(run_id).get("statistics", {}) for run_id in run_ids}
