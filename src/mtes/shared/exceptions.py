"""Module-local typed exceptions for MTES."""


class MtesError(Exception):
    """Base exception for MTES application errors."""


class ConfigurationError(MtesError):
    """Raised when configuration is missing or invalid."""


class InvalidGenomeError(MtesError):
    """Raised when a genome fails structural validation."""


class ConstraintViolationError(MtesError):
    """Raised when phenotype output violates constraints."""


class MongoDbUnavailableError(MtesError):
    """Raised when MongoDB is unreachable or returns fatal errors."""


class ProviderUnavailableError(MtesError):
    """Raised when an LLM or embedding provider is unavailable."""


class TelegramGatewayUnavailableError(MtesError):
    """Raised when Telegram integration fails."""
