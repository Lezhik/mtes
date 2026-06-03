"""Single phenotype generation pipeline (mapping → LLM → validation → fitness)."""

from dataclasses import dataclass
from typing import Any

from mtes.llm.candidate_expansion_service import CandidateExpansionService, RankedCandidate
from mtes.llm.constraint_expansion_service import ConstraintExpansionService
from mtes.llm.phenotype_compiler import PhenotypeCompiler
from mtes.llm.provider_chain import LlmAdapterService, LlmProviderChain
from mtes.mapping.fitness_evaluator import FitnessEvaluator, FitnessInputs, FitnessResult
from mtes.mapping.structural_plan_service import StructuralPlanService
from mtes.mapping.translation_service import translate_numeric_genes
from mtes.mapping.validation_service import ValidationService
from mtes.shared.types import Genome


@dataclass(frozen=True, slots=True)
class GenerationPipelineResult:
    genome_id: str
    selected_candidate: RankedCandidate
    compiled_text: str
    routing_family: str
    constraint_set: dict[str, Any]
    validation_anchor_integrity: float
    fitness: FitnessResult
    structural_plan: dict[str, Any]


class GenerationPipeline:
    """Orchestrate one full phenotype generation without direct provider calls."""

    def __init__(
        self,
        llm_adapter_service: LlmAdapterService,
        *,
        structural_plan_service: StructuralPlanService | None = None,
        validation_service: ValidationService | None = None,
        fitness_evaluator: FitnessEvaluator | None = None,
    ) -> None:
        self._constraint_expansion = ConstraintExpansionService(llm_adapter_service)
        self._phenotype_compiler = PhenotypeCompiler(llm_adapter_service)
        self._candidate_expansion = CandidateExpansionService(llm_adapter_service)
        self._structural_plan_service = structural_plan_service or StructuralPlanService()
        self._validation_service = validation_service or ValidationService()
        self._fitness_evaluator = fitness_evaluator or FitnessEvaluator()

    async def run(self, genome: Genome) -> GenerationPipelineResult:
        constraint_set = await self._constraint_expansion.expand_constraints(genome)
        constraints = translate_numeric_genes(genome.numeric_genes)
        anchors = tuple(gene.anchor for gene in genome.semantic_genes)
        plan = self._structural_plan_service.build_plan(
            anchors=anchors,
            relation_counts={},
            short_clause_ratio=constraints.short_clause_ratio,
            required_sentiment_shift=constraints.required_sentiment_shift,
        )
        structural_plan = {
            "anchors": list(plan.anchors),
            "relation_focus": plan.relation_focus.value,
            "rhetorical_mode": plan.rhetorical_mode.value,
            "sentiment_pattern": plan.sentiment_pattern.value,
        }
        compiled = await self._phenotype_compiler.compile_phenotype(
            genome,
            constraint_set,
            structural_plan=structural_plan,
        )
        candidate_text = str(compiled["candidate_text"])
        routing_family = str(compiled["routing_family"])
        base_embedding = (1.0, 0.0, 0.0, 0.0)
        ranked = await self._candidate_expansion.expand_candidates(
            genome_id=genome.genome_id,
            base_candidate_text=candidate_text,
            constraint_set=constraint_set,
            routing_family=routing_family,
            base_embedding=base_embedding,
            candidate_embeddings=[base_embedding] * 5,
            llm_responses=[
                candidate_text,
                f"{candidate_text} variant a",
                f"{candidate_text} variant b",
                f"{candidate_text} variant c",
                f"{candidate_text} variant d",
            ],
        )
        selected = next(candidate for candidate in ranked if candidate.selected)
        validation = self._validation_service.validate_candidate(
            candidate_text=selected.candidate_text,
            required_anchors=anchors,
            constraints=constraints,
        )
        fitness = self._fitness_evaluator.calculate_fitness(
            FitnessInputs(
                candidate_text=selected.candidate_text,
                anchor_integrity=validation.anchor_integrity,
                local_novelty=selected.diversity_score,
            ),
            constraints,
        )
        return GenerationPipelineResult(
            genome_id=genome.genome_id,
            selected_candidate=selected,
            compiled_text=candidate_text,
            routing_family=routing_family,
            constraint_set=constraint_set,
            validation_anchor_integrity=validation.anchor_integrity,
            fitness=fitness,
            structural_plan=structural_plan,
        )
