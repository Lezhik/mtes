"""Operational report generation per SRS §9."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class EvolutionSummary:
    generation_number: int
    fitness_mean: float
    fitness_std: float
    locality_correlation: float
    locality_correlation_std: float
    anchor_integrity_mean: float


@dataclass(frozen=True, slots=True)
class RecentContentEntry:
    generation_number: int
    fitness_score: float
    novelty_score: float
    anchor_integrity: float
    text: str


@dataclass(frozen=True, slots=True)
class ReportSnapshot:
    evolution_summary: EvolutionSummary
    recent_content: tuple[RecentContentEntry, ...]
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class ReportArtifacts:
    json_path: Path
    html_path: Path
    snapshot: ReportSnapshot


class ReportDataSource(Protocol):
    async def load_snapshot(self) -> ReportSnapshot:
        ...


@dataclass
class InMemoryReportDataSource:
    """Fixture-backed report data for tests and offline generation."""

    snapshot: ReportSnapshot

    async def load_snapshot(self) -> ReportSnapshot:
        return self.snapshot


class ReportService:
    """Build HTML and JSON operational reports under ./reports/."""

    def __init__(
        self,
        data_source: ReportDataSource,
        *,
        output_dir: Path | None = None,
    ) -> None:
        self._data_source = data_source
        self._output_dir = output_dir or Path("reports")

    async def generate_reports(self) -> ReportArtifacts:
        snapshot = await self._data_source.load_snapshot()
        self._output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = snapshot.generated_at.strftime("%Y%m%dT%H%M%SZ")
        json_path = self._output_dir / f"mtes_report_{timestamp}.json"
        html_path = self._output_dir / f"mtes_report_{timestamp}.html"
        json_path.write_text(
            json.dumps(self.build_json_document(snapshot), indent=2),
            encoding="utf-8",
        )
        html_path.write_text(self.build_html_document(snapshot), encoding="utf-8")
        return ReportArtifacts(json_path=json_path, html_path=html_path, snapshot=snapshot)

    def build_json_document(self, snapshot: ReportSnapshot) -> dict[str, Any]:
        summary = snapshot.evolution_summary
        return {
            "generated_at": snapshot.generated_at.isoformat(),
            "evolution_summary": {
                "generation_number": summary.generation_number,
                "fitness_mean": summary.fitness_mean,
                "fitness_std": summary.fitness_std,
                "locality_correlation": summary.locality_correlation,
                "locality_correlation_std": summary.locality_correlation_std,
                "anchor_integrity_mean": summary.anchor_integrity_mean,
            },
            "recent_content": [
                {
                    "generation_number": entry.generation_number,
                    "fitness_score": entry.fitness_score,
                    "novelty_score": entry.novelty_score,
                    "anchor_integrity": entry.anchor_integrity,
                    "text": entry.text,
                }
                for entry in snapshot.recent_content
            ],
        }

    def build_html_document(self, snapshot: ReportSnapshot) -> str:
        summary = snapshot.evolution_summary
        locality_line = (
            f"{summary.locality_correlation:.2f} ± {summary.locality_correlation_std:.2f}"
        )
        rows = "".join(
            (
                "<tr>"
                f"<td>{entry.generation_number}</td>"
                f"<td>{entry.fitness_score:.3f}</td>"
                f"<td>{entry.novelty_score:.3f}</td>"
                f"<td>{entry.anchor_integrity:.3f}</td>"
                f"<td>{_escape_html(entry.text)}</td>"
                "</tr>"
            )
            for entry in snapshot.recent_content
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>MTES Operational Report</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
  </style>
</head>
<body>
  <h1>MTES Operational Report</h1>
  <p>Generated at: {snapshot.generated_at.isoformat()}</p>
  <h2>Evolution Summary</h2>
  <ul>
    <li>Generation: {summary.generation_number}</li>
    <li>Fitness mean: {summary.fitness_mean:.3f}</li>
    <li>Fitness std: {summary.fitness_std:.3f}</li>
    <li>Locality correlation: {locality_line}</li>
    <li>Anchor integrity mean: {summary.anchor_integrity_mean:.3f}</li>
  </ul>
  <h2>Recent Generated Content</h2>
  <table>
    <thead>
      <tr>
        <th>Generation</th><th>Fitness</th><th>Novelty</th><th>Anchor integrity</th><th>Text</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def default_fixture_snapshot() -> ReportSnapshot:
    """Default snapshot for CLI when no database source is configured."""
    return ReportSnapshot(
        evolution_summary=EvolutionSummary(
            generation_number=0,
            fitness_mean=0.0,
            fitness_std=0.0,
            locality_correlation=0.0,
            locality_correlation_std=0.0,
            anchor_integrity_mean=0.0,
        ),
        recent_content=(),
        generated_at=datetime.now(UTC),
    )
