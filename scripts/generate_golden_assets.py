#!/usr/bin/env python3
"""Generate golden benchmark assets per Bootstrap §9–10."""

from __future__ import annotations

import json
import random
from pathlib import Path

GENOME_COUNT = 500
PROMPT_COUNT = 100
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "golden"

ANCHORS = (
    "winter",
    "silence",
    "frost",
    "ember",
    "wind",
    "river",
    "stone",
    "dawn",
    "shadow",
    "glass",
)
ROUTING_FAMILIES = ("P1-A", "P2-B", "P3-C", "P4-D", "P4-E")


def _lhs_coordinate(rng: random.Random) -> list[int]:
    return [rng.randint(0, 7) for _ in range(5)]


def _numeric_genes(rng: random.Random) -> dict[str, float]:
    return {
        "fragmentation_bias": round(rng.uniform(0.3, 0.7), 3),
        "ambiguity_bias": round(rng.uniform(0.3, 0.7), 3),
        "sentiment_contrast": round(rng.uniform(0.3, 0.7), 3),
        "semantic_jump_radius": round(rng.uniform(0.3, 0.7), 3),
        "compression_target": round(rng.uniform(0.3, 0.7), 3),
        "anchor_rigidity": round(rng.uniform(0.3, 0.7), 3),
    }


def generate_genomes(path: Path, *, count: int, seed: int) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for index in range(count):
            genome_id = f"golden_{index:04d}"
            anchor = rng.choice(ANCHORS)
            coordinate = _lhs_coordinate(rng)
            record = {
                "genome_id": genome_id,
                "generation": 0,
                "semantic_genes": [
                    {"gene_id": 1, "coordinate": coordinate, "anchor": anchor},
                ],
                "numeric_genes": _numeric_genes(rng),
                "phenotype_text": f"{anchor} signal {index}",
                "embedding": [
                    round(rng.uniform(-1.0, 1.0), 4),
                    round(rng.uniform(-1.0, 1.0), 4),
                    round(rng.uniform(-1.0, 1.0), 4),
                ],
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def generate_prompts(path: Path, *, count: int, seed: int) -> None:
    rng = random.Random(seed + 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for index in range(count):
            family = rng.choice(ROUTING_FAMILIES)
            record = {
                "prompt_id": f"gp_{index:04d}",
                "routing_family": family,
                "template_version": "1.0",
                "body": f"Compile phenotype under {family} constraints (case {index}).",
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    generate_genomes(OUTPUT_DIR / "genomes.jsonl", count=GENOME_COUNT, seed=42)
    generate_prompts(OUTPUT_DIR / "prompts.jsonl", count=PROMPT_COUNT, seed=42)
    print(f"Wrote {GENOME_COUNT} genomes and {PROMPT_COUNT} prompts to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
