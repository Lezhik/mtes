"""Deterministic numeric gene translation per Mapping Specification §4."""

from dataclasses import dataclass

from mtes.mapping.numeric_lut import byte_to_gene_value, gene_value_to_byte
from mtes.shared.types import NumericGenes

# Mapping Spec §3.2 MVP defaults.
MVP_NUMERIC_DEFAULTS = NumericGenes(
    fragmentation_bias=0.50,
    ambiguity_bias=0.45,
    sentiment_contrast=0.40,
    semantic_jump_radius=0.35,
    compression_target=0.55,
    anchor_rigidity=0.70,
)


@dataclass(frozen=True, slots=True)
class TranslatedConstraints:
    """Deterministic constraints derived from numeric genes."""

    punctuation_density: float
    short_clause_ratio: float
    semantic_entropy_target: float
    indirect_reference_ratio: float
    required_sentiment_shift: float
    semantic_expansion_radius: float
    target_information_density: float
    target_token_limit: int
    anchor_similarity_threshold: float


def compression_token_limit(compression_target: float) -> int:
    """Mapping Spec §4.3 compression tiers."""
    if compression_target <= 0.30:
        return 48
    if compression_target <= 0.60:
        return 36
    return 24


def anchor_similarity_threshold(anchor_rigidity: float) -> float:
    """Mapping Spec v5.0 §1: 0.82 + anchor_rigidity * 0.14."""
    return 0.82 + (anchor_rigidity * 0.14)


def translate_numeric_genes(genes: NumericGenes) -> TranslatedConstraints:
    """Convert six operational genes into deterministic constraint targets."""
    return TranslatedConstraints(
        punctuation_density=genes.fragmentation_bias,
        short_clause_ratio=genes.fragmentation_bias,
        semantic_entropy_target=genes.ambiguity_bias,
        indirect_reference_ratio=genes.ambiguity_bias,
        required_sentiment_shift=genes.sentiment_contrast,
        semantic_expansion_radius=genes.semantic_jump_radius,
        target_information_density=genes.compression_target,
        target_token_limit=compression_token_limit(genes.compression_target),
        anchor_similarity_threshold=anchor_similarity_threshold(genes.anchor_rigidity),
    )


def numeric_genes_from_bytes(
    *,
    fragmentation_bias: int,
    ambiguity_bias: int,
    sentiment_contrast: int,
    semantic_jump_radius: int,
    compression_target: int,
    anchor_rigidity: int,
) -> NumericGenes:
    """Build NumericGenes from persisted uint8 gene bytes."""
    return NumericGenes(
        fragmentation_bias=byte_to_gene_value(fragmentation_bias),
        ambiguity_bias=byte_to_gene_value(ambiguity_bias),
        sentiment_contrast=byte_to_gene_value(sentiment_contrast),
        semantic_jump_radius=byte_to_gene_value(semantic_jump_radius),
        compression_target=byte_to_gene_value(compression_target),
        anchor_rigidity=byte_to_gene_value(anchor_rigidity),
    )


def numeric_genes_to_bytes(genes: NumericGenes) -> dict[str, int]:
    """Encode NumericGenes to uint8 bytes for persistence."""
    return {
        "fragmentation_bias": gene_value_to_byte(genes.fragmentation_bias),
        "ambiguity_bias": gene_value_to_byte(genes.ambiguity_bias),
        "sentiment_contrast": gene_value_to_byte(genes.sentiment_contrast),
        "semantic_jump_radius": gene_value_to_byte(genes.semantic_jump_radius),
        "compression_target": gene_value_to_byte(genes.compression_target),
        "anchor_rigidity": gene_value_to_byte(genes.anchor_rigidity),
    }
