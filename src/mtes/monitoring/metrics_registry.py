"""Prometheus metrics per SRS §10."""

from prometheus_client import Counter, Gauge, Info

GENERATION_TOTAL = Counter(
    "mtes_generation_total",
    "Total phenotype generation attempts",
)
PUBLICATION_TOTAL = Counter(
    "mtes_publication_total",
    "Total Telegram publications",
)
VALIDATION_PASS_TOTAL = Counter(
    "mtes_validation_pass_total",
    "Total validation passes",
)
REPAIR_TOTAL = Counter(
    "mtes_repair_total",
    "Total repair operations",
)
DATABASE_FAILURES_TOTAL = Counter(
    "mtes_database_failures_total",
    "Total database failures",
)
TELEGRAM_FAILURES_TOTAL = Counter(
    "mtes_telegram_failures_total",
    "Total Telegram failures",
)

POPULATION_GENERATION = Gauge(
    "mtes_population_generation",
    "Current evolution generation number",
)
FITNESS_MEAN = Gauge(
    "mtes_fitness_mean",
    "Mean fitness of current population",
)
FITNESS_STD = Gauge(
    "mtes_fitness_std",
    "Fitness standard deviation of current population",
)
ANCHOR_INTEGRITY_MEAN = Gauge(
    "mtes_anchor_integrity_mean",
    "Mean anchor integrity of recent candidates",
)
LOCALITY_CORRELATION = Gauge(
    "mtes_locality_correlation",
    "Latest measured genotype-phenotype locality correlation",
)
REPAIR_RATE = Gauge(
    "mtes_repair_rate",
    "Repair rate over recent evaluation window",
)

PROVIDER_INFO = Info(
    "mtes_provider",
    "Active LLM provider metadata",
)
