"""Report generation tests."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from mtes.core.report_service import (
    EvolutionSummary,
    InMemoryReportDataSource,
    RecentContentEntry,
    ReportService,
    ReportSnapshot,
)


@pytest.fixture
def snapshot() -> ReportSnapshot:
    return ReportSnapshot(
        evolution_summary=EvolutionSummary(
            generation_number=12,
            fitness_mean=0.71,
            fitness_std=0.08,
            locality_correlation=0.52,
            locality_correlation_std=0.03,
            anchor_integrity_mean=0.88,
        ),
        recent_content=(
            RecentContentEntry(
                generation_number=12,
                fitness_score=0.74,
                novelty_score=0.61,
                anchor_integrity=0.90,
                text="winter silence drifts",
            ),
        ),
        generated_at=datetime(2026, 6, 3, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_generate_reports_writes_json_and_html(
    snapshot: ReportSnapshot,
    tmp_path: Path,
) -> None:
    service = ReportService(
        InMemoryReportDataSource(snapshot),
        output_dir=tmp_path,
    )
    artifacts = await service.generate_reports()
    assert artifacts.json_path.exists()
    assert artifacts.html_path.exists()
    assert "locality_correlation" in artifacts.json_path.read_text(encoding="utf-8")
    assert "0.52" in artifacts.html_path.read_text(encoding="utf-8")
