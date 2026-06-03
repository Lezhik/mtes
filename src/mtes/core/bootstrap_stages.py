"""Bootstrap pipeline stage definitions per Bootstrap Specification §4."""

from enum import StrEnum


class BootstrapStage(StrEnum):
    INFRASTRUCTURE_VALIDATION = "infrastructure_validation"
    PROVIDER_VALIDATION = "provider_validation"
    DICTIONARY_CONSTRUCTION = "dictionary_construction"
    EMBEDDING_VALIDATION = "embedding_validation"
    GOLDEN_DATASET_CREATION = "golden_dataset_creation"
    GOLDEN_PROMPT_SET_CREATION = "golden_prompt_set_creation"
    LOCALITY_CALIBRATION = "locality_calibration"
    CALIBRATION_TWEET_GENERATION = "calibration_tweet_generation"
    INITIAL_POPULATION_GENERATION = "initial_population_generation"
    TELEGRAM_VALIDATION = "telegram_validation"
    TRIAL_PUBLICATIONS = "trial_publications"
    READINESS_EVALUATION = "readiness_evaluation"
    BOOTSTRAP_REPORT = "bootstrap_report"


BOOTSTRAP_STAGE_ORDER: tuple[BootstrapStage, ...] = (
    BootstrapStage.INFRASTRUCTURE_VALIDATION,
    BootstrapStage.PROVIDER_VALIDATION,
    BootstrapStage.DICTIONARY_CONSTRUCTION,
    BootstrapStage.EMBEDDING_VALIDATION,
    BootstrapStage.GOLDEN_DATASET_CREATION,
    BootstrapStage.GOLDEN_PROMPT_SET_CREATION,
    BootstrapStage.LOCALITY_CALIBRATION,
    BootstrapStage.CALIBRATION_TWEET_GENERATION,
    BootstrapStage.INITIAL_POPULATION_GENERATION,
    BootstrapStage.TELEGRAM_VALIDATION,
    BootstrapStage.TRIAL_PUBLICATIONS,
    BootstrapStage.READINESS_EVALUATION,
    BootstrapStage.BOOTSTRAP_REPORT,
)
