from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(tags=["evaluation"])

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "evaluation" / "integration" / "results"


@router.get("/results")
async def get_evaluation_results():
    """Return the latest real integration evaluation results."""
    if not RESULTS_DIR.exists():
        return {"total_scenarios": 0, "passed": 0, "failed": 0, "skipped": 0, "by_category": {}, "total_duration_ms": 0, "timestamp": None, "results": []}

    json_files = sorted(RESULTS_DIR.glob("real_integration_*.json"), reverse=True)
    if not json_files:
        return {"total_scenarios": 0, "passed": 0, "failed": 0, "skipped": 0, "by_category": {}, "total_duration_ms": 0, "timestamp": None, "results": []}

    latest = json_files[0]
    try:
        with open(latest) as f:
            data = json.load(f)
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read evaluation results file")
