"""Shared domain types."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EvolutionStatus(StrEnum):
    """Evolution lifecycle states per SRS §7.2."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    RESETTING = "RESETTING"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class SemanticGene:
    """Single semantic gene with coordinate and resolved anchor."""

    gene_id: int
    coordinate: tuple[int, int, int, int, int]
    anchor: str


@dataclass(frozen=True, slots=True)
class NumericGenes:
    """Six operational numeric genes (MVP)."""

    fragmentation_bias: float
    ambiguity_bias: float
    sentiment_contrast: float
    semantic_jump_radius: float
    compression_target: float
    anchor_rigidity: float


@dataclass(frozen=True, slots=True)
class Genome:
    """Genotype representation for pipeline and persistence."""

    genome_id: str
    generation: int
    semantic_genes: tuple[SemanticGene, ...]
    numeric_genes: NumericGenes
    parent_ids: tuple[str, ...] = field(default_factory=tuple)
    seed: int = 0
    dictionary_version: str = ""
    mapping_version: str = ""


@dataclass(frozen=True, slots=True)
class Candidate:
    """Phenotype candidate before or after validation."""

    candidate_id: str
    genome_id: str
    text: str
    routing_family: str = ""
    prompt_version: str = ""
    validation_status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
