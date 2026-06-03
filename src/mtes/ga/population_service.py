"""Population management for evolutionary cycles."""

from dataclasses import dataclass, field

from mtes.shared.types import Genome


@dataclass
class PopulationService:
    """Maintain in-memory population state."""

    target_size: int
    members: list[Genome] = field(default_factory=list)
    generation_number: int = 0

    @property
    def population_size(self) -> int:
        return len(self.members)

    def add_member(self, genome: Genome) -> None:
        self.members.append(genome)
        if len(self.members) > self.target_size:
            self.members.sort(key=lambda item: item.generation, reverse=True)
            self.members = self.members[: self.target_size]

    def replace_population(self, genomes: list[Genome]) -> None:
        self.members = genomes[: self.target_size]
        if self.members:
            self.generation_number = max(genome.generation for genome in self.members)

    def advance_generation(self) -> int:
        self.generation_number += 1
        return self.generation_number
