"""Provider scoring per Bootstrap Specification §6.5–6.7."""

from dataclasses import dataclass

# Bootstrap §6.5
PRELIMINARY_RELIABILITY_WEIGHT = 0.50
PRELIMINARY_ANCHOR_WEIGHT = 0.20
PRELIMINARY_REPAIR_WEIGHT = 0.15
PRELIMINARY_LATENCY_WEIGHT = 0.15

# Bootstrap §6.6
FINAL_RELIABILITY_WEIGHT = 0.40
FINAL_LOCALITY_WEIGHT = 0.25
FINAL_ANCHOR_WEIGHT = 0.15
FINAL_REPAIR_WEIGHT = 0.10
FINAL_LATENCY_WEIGHT = 0.10

MANDATORY_PROVIDER_SUCCESS_RATE = 0.95
MANDATORY_SCHEMA_COMPLIANCE = 0.98
MANDATORY_ANCHOR_INTEGRITY = 0.85
MANDATORY_REPAIR_RATE_MAX = 0.10
MANDATORY_LOCALITY_CORRELATION = 0.45


@dataclass(frozen=True, slots=True)
class ProviderValidationMetrics:
    """Observed provider metrics during bootstrap validation."""

    provider_id: str
    provider_success_rate: float
    schema_compliance: float
    anchor_integrity: float
    repair_rate: float
    latency_mean_seconds: float
    locality_correlation: float | None = None


def reliability_score(metrics: ProviderValidationMetrics) -> float:
    return metrics.provider_success_rate


def anchor_score(metrics: ProviderValidationMetrics) -> float:
    return metrics.anchor_integrity


def repair_score(metrics: ProviderValidationMetrics) -> float:
    return max(0.0, 1.0 - metrics.repair_rate)


def latency_score(metrics: ProviderValidationMetrics, *, latency_reference_seconds: float) -> float:
    if latency_reference_seconds <= 0:
        return 0.0
    ratio = metrics.latency_mean_seconds / latency_reference_seconds
    return 1.0 - min(ratio, 1.0)


def calculate_preliminary_provider_score(
    metrics: ProviderValidationMetrics,
    *,
    latency_reference_seconds: float,
) -> float:
    """Bootstrap §6.5 preliminary score (before locality calibration)."""
    return (
        PRELIMINARY_RELIABILITY_WEIGHT * reliability_score(metrics)
        + PRELIMINARY_ANCHOR_WEIGHT * anchor_score(metrics)
        + PRELIMINARY_REPAIR_WEIGHT * repair_score(metrics)
        + PRELIMINARY_LATENCY_WEIGHT
        * latency_score(metrics, latency_reference_seconds=latency_reference_seconds)
    )


def calculate_final_provider_score(
    metrics: ProviderValidationMetrics,
    *,
    latency_reference_seconds: float,
) -> float:
    """Bootstrap §6.6 final score (requires locality_correlation)."""
    if metrics.locality_correlation is None:
        raise ValueError("locality_correlation is required for final provider score")
    locality = metrics.locality_correlation
    return (
        FINAL_RELIABILITY_WEIGHT * reliability_score(metrics)
        + FINAL_LOCALITY_WEIGHT * locality
        + FINAL_ANCHOR_WEIGHT * anchor_score(metrics)
        + FINAL_REPAIR_WEIGHT * repair_score(metrics)
        + FINAL_LATENCY_WEIGHT
        * latency_score(metrics, latency_reference_seconds=latency_reference_seconds)
    )


def passes_mandatory_provider_thresholds(metrics: ProviderValidationMetrics) -> bool:
    """Bootstrap §6.4 mandatory gates for default provider eligibility."""
    if metrics.provider_success_rate < MANDATORY_PROVIDER_SUCCESS_RATE:
        return False
    if metrics.schema_compliance < MANDATORY_SCHEMA_COMPLIANCE:
        return False
    if metrics.anchor_integrity < MANDATORY_ANCHOR_INTEGRITY:
        return False
    if metrics.repair_rate > MANDATORY_REPAIR_RATE_MAX:
        return False
    if metrics.locality_correlation is not None:
        if metrics.locality_correlation < MANDATORY_LOCALITY_CORRELATION:
            return False
    return True


def rank_providers_by_score(scores: dict[str, float]) -> list[tuple[str, float]]:
    """Return providers sorted by score descending."""
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def select_default_provider(
    metrics_by_provider: dict[str, ProviderValidationMetrics],
    *,
    latency_reference_seconds: float,
    use_final_scores: bool,
) -> str | None:
    """Bootstrap §6.8: highest score among providers passing mandatory thresholds."""
    scores: dict[str, float] = {}
    for provider_id, metrics in metrics_by_provider.items():
        if not passes_mandatory_provider_thresholds(metrics):
            continue
        if use_final_scores:
            if metrics.locality_correlation is None:
                continue
            score = calculate_final_provider_score(
                metrics, latency_reference_seconds=latency_reference_seconds
            )
        else:
            score = calculate_preliminary_provider_score(
                metrics, latency_reference_seconds=latency_reference_seconds
            )
        scores[provider_id] = score
    ranked = rank_providers_by_score(scores)
    if not ranked:
        return None
    return ranked[0][0]
