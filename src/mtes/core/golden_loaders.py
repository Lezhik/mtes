"""Load golden dataset and prompt fixtures (JSONL)."""

import json
from dataclasses import dataclass
from pathlib import Path

from mtes.shared.types import Genome, NumericGenes, SemanticGene


@dataclass(frozen=True, slots=True)
class GoldenDatasetRecord:
    """Single golden genome with compiled phenotype and cached embedding."""

    genome: Genome
    phenotype_text: str
    embedding: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class GoldenPromptRecord:
    prompt_id: str
    routing_family: str
    template_version: str
    body: str


def _parse_semantic_genes(raw: list[dict[str, object]]) -> tuple[SemanticGene, ...]:
    genes: list[SemanticGene] = []
    for item in raw:
        coordinate_raw = item["coordinate"]
        if not isinstance(coordinate_raw, list):
            raise ValueError("coordinate must be a list of five integers")
        coordinate = tuple(int(value) for value in coordinate_raw)
        genes.append(
            SemanticGene(
                gene_id=int(item["gene_id"]),
                coordinate=(coordinate[0], coordinate[1], coordinate[2], coordinate[3], coordinate[4]),
                anchor=str(item["anchor"]),
            )
        )
    return tuple(genes)


def _parse_numeric_genes(raw: dict[str, object]) -> NumericGenes:
    return NumericGenes(
        fragmentation_bias=float(raw["fragmentation_bias"]),
        ambiguity_bias=float(raw["ambiguity_bias"]),
        sentiment_contrast=float(raw["sentiment_contrast"]),
        semantic_jump_radius=float(raw["semantic_jump_radius"]),
        compression_target=float(raw["compression_target"]),
        anchor_rigidity=float(raw["anchor_rigidity"]),
    )


def _parse_genome(raw: dict[str, object]) -> Genome:
    return Genome(
        genome_id=str(raw["genome_id"]),
        generation=int(raw.get("generation", 0)),
        semantic_genes=_parse_semantic_genes(raw["semantic_genes"]),  # type: ignore[arg-type]
        numeric_genes=_parse_numeric_genes(raw["numeric_genes"]),  # type: ignore[arg-type]
        parent_ids=tuple(str(parent) for parent in raw.get("parent_ids", [])),
        seed=int(raw.get("seed", 0)),
        dictionary_version=str(raw.get("dictionary_version", "")),
        mapping_version=str(raw.get("mapping_version", "")),
    )


def load_golden_dataset(path: Path) -> tuple[GoldenDatasetRecord, ...]:
    """Load golden dataset JSONL (one JSON object per line)."""
    records: list[GoldenDatasetRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"Line {line_number}: expected JSON object")
            embedding_raw = payload.get("embedding")
            if not isinstance(embedding_raw, list):
                raise ValueError(f"Line {line_number}: embedding must be a list of floats")
            records.append(
                GoldenDatasetRecord(
                    genome=_parse_genome(payload),
                    phenotype_text=str(payload["phenotype_text"]),
                    embedding=tuple(float(value) for value in embedding_raw),
                )
            )
    return tuple(records)


def load_golden_prompts(path: Path) -> tuple[GoldenPromptRecord, ...]:
    """Load golden prompt set JSONL."""
    records: list[GoldenPromptRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"Line {line_number}: expected JSON object")
            records.append(
                GoldenPromptRecord(
                    prompt_id=str(payload["prompt_id"]),
                    routing_family=str(payload["routing_family"]),
                    template_version=str(payload["template_version"]),
                    body=str(payload["body"]),
                )
            )
    return tuple(records)
