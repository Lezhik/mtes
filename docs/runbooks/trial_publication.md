# Trial Publication Runbook (Bootstrap §15)

## Purpose

Validate production Telegram behavior before full evolution launch.

## Preconditions

- Bootstrap readiness: `READY` or approved `READY_WITH_WARNINGS`
- `MTES_OPERATOR_TOKEN` and `MTES_OPERATOR_ALLOW_LIST` configured
- Telegram channel credentials configured in deployment config

## Procedure

1. Start daemon: `mtes daemon start`
2. Enqueue trial posts (50–200) via publication service or `mtes telegram publish`
3. Observe for **≥ 7 days** (wall-clock observation window)
4. Collect metrics from `GET /metrics`:
   - `mtes_publication_total`
   - `mtes_telegram_failures_total`
5. Record operator notes in bootstrap report if thresholds are borderline

## Mandatory thresholds

| Metric | Threshold |
|--------|-----------|
| `publication_success_rate` | ≥ 0.99 |
| `engagement_collection_success_rate` | ≥ 0.95 |

Compute `publication_success_rate` as successful publishes divided by attempted publishes during the trial window.

## Waiver

If a mandatory threshold is not met, document a waiver with:

- operator approval timestamp
- operator notes
- remediation plan

Production evolution MUST NOT start until waiver is recorded or thresholds pass.
