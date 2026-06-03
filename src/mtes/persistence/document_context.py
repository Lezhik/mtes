"""Common document metadata per Data Model Specification §2.1."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class DocumentContext:
    """Values injected into every persisted document."""

    schema_version: str
    experiment_id: str
    run_id: str

    def stamp(self, document: dict[str, object]) -> dict[str, object]:
        """Return a copy of document with common fields set."""
        stamped = dict(document)
        stamped["schema_version"] = self.schema_version
        stamped["experiment_id"] = self.experiment_id
        stamped["run_id"] = self.run_id
        stamped["created_at"] = datetime.now(UTC).isoformat()
        return stamped
