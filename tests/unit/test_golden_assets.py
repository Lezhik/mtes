"""Golden asset smoke tests for bootstrap locality stage."""

from pathlib import Path

from mtes.core.golden_loaders import load_golden_dataset, load_golden_prompts
from mtes.core.locality_calibration import LocalityCalibrationService, expected_pair_count

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "data" / "golden"
SMOKE_GENOME_LIMIT = 20


def test_golden_assets_meet_minimum_counts() -> None:
    genomes_path = GOLDEN_DIR / "genomes.jsonl"
    prompts_path = GOLDEN_DIR / "prompts.jsonl"
    genome_lines = [line for line in genomes_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    prompt_lines = [line for line in prompts_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(genome_lines) >= 500
    assert len(prompt_lines) >= 100


def test_locality_smoke_subset_runs_on_committed_golden_set() -> None:
    records = load_golden_dataset(GOLDEN_DIR / "genomes.jsonl")[:SMOKE_GENOME_LIMIT]
    result = LocalityCalibrationService().calibrate_once(records)
    assert result.pair_count == expected_pair_count(len(records))
    assert -1.0 <= result.locality_correlation <= 1.0


def test_golden_prompts_load() -> None:
    prompts = load_golden_prompts(GOLDEN_DIR / "prompts.jsonl")
    assert len(prompts) >= 100
