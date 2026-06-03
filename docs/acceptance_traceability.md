# SRS §20 Acceptance Traceability Matrix

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Bootstrap succeeds | `tests/unit/test_bootstrap_module.py`, `mtes bootstrap --dry-run` | Implemented |
| Generation succeeds | `tests/unit/test_generation_pipeline.py`, `tests/integration/test_pipeline_evolution.py` | Implemented |
| Evolution control succeeds | `tests/unit/test_workflow_coordinator.py`, `tests/unit/test_cli.py` | Implemented |
| Daemon execution succeeds | `tests/unit/test_daemon_service.py`, `mtes daemon start` | Implemented |
| Daemon recovery succeeds | `WorkflowCoordinator.recover_workflows_on_startup` + integration workflow tests | Implemented |
| Publication succeeds | `tests/unit/test_telegram_publication.py` | Implemented |
| Statistics collection succeeds | Telegram stats command stub; metrics via Prometheus | Partial |
| Health endpoint functions | `tests/unit/test_monitoring_http.py` | Implemented |
| Metrics endpoint functions | `tests/unit/test_monitoring_http.py` | Implemented |
| HTML reports generated | `tests/unit/test_report_service.py`, `mtes report` | Implemented |
| JSON reports generated | `tests/unit/test_report_service.py`, `mtes report --json` | Implemented |
| Audit logging functions | `tests/unit/test_llm_provider_chain.py` (InMemoryAuditWriter) | Implemented |
| Graceful shutdown functions | `tests/unit/test_daemon_service.py` | Implemented |
| Trial publication window | `docs/runbooks/trial_publication.md` | Runbook (manual) |
| Golden assets reproducibility | `data/golden/*.jsonl`, `scripts/generate_golden_assets.py` | Implemented |

## CI commands

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q   # requires Docker
```

## Known gaps

- Live Telegram trial metrics require operator execution on VPS (§15).
- Full 500-genome locality calibration smoke uses subset in CI; full run documented in `DEVELOPMENT_PLAN.md` Step 13.2.
