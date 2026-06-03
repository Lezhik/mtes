"""Numeric gene LUT per Genetic Encoding Specification §6."""

import math

LUT_VERSION = "1.0"
LUT_STEEPNESS = 1.25

# GA Spec §6.6 verification checkpoints (byte -> expected value).
LUT_CHECKPOINTS: tuple[tuple[int, float], ...] = (
    (0, 0.223),
    (32, 0.283),
    (64, 0.351),
    (96, 0.425),
    (128, 0.501),
    (160, 0.577),
    (192, 0.649),
    (208, 0.682),
    (224, 0.717),
    (255, 0.777),
)

# GA §6.6 table values are rounded to three decimals; formula may differ slightly.
CHECKPOINT_TOLERANCE = 0.002
ROUND_TRIP_MAX_BYTE_ERROR = 1


def byte_to_unit(byte_value: int) -> float:
    """Map uint8 storage byte to unit interval [0, 1]."""
    if not 0 <= byte_value <= 255:
        raise ValueError(f"byte_value must be in [0, 255], got {byte_value}")
    return byte_value / 255.0


def unit_to_gene_value(unit: float) -> float:
    """Canonical LUT: u -> 0.5 + 0.5*tanh(1.25*(u - 0.5))."""
    if not 0.0 <= unit <= 1.0:
        raise ValueError(f"unit must be in [0.0, 1.0], got {unit}")
    return 0.5 + 0.5 * math.tanh(LUT_STEEPNESS * (unit - 0.5))


def byte_to_gene_value(byte_value: int) -> float:
    """Decode stored uint8 gene byte to runtime float64 value."""
    return unit_to_gene_value(byte_to_unit(byte_value))


def gene_value_to_byte(gene_value: float) -> int:
    """Encode runtime gene value to nearest uint8 byte (round-trip <= 1 byte)."""
    if not 0.0 <= gene_value <= 1.0:
        raise ValueError(f"gene_value must be in [0.0, 1.0], got {gene_value}")

    best_byte = 0
    best_distance = float("inf")
    for candidate_byte in range(256):
        candidate_value = byte_to_gene_value(candidate_byte)
        distance = abs(candidate_value - gene_value)
        if distance < best_distance:
            best_distance = distance
            best_byte = candidate_byte
    return best_byte


def serialize_gene_value(gene_value: float) -> float:
    """Serialize runtime value to six decimal places per GA §6.4."""
    return round(gene_value, 6)


def verify_lut_checkpoints() -> None:
    """Validate LUT against GA reference points; raises on drift."""
    for byte_value, expected in LUT_CHECKPOINTS:
        actual = byte_to_gene_value(byte_value)
        if abs(actual - expected) > CHECKPOINT_TOLERANCE:
            raise ValueError(
                f"LUT checkpoint mismatch at byte={byte_value}: "
                f"expected={expected}, actual={actual}"
            )


def round_trip_byte_error(gene_value: float) -> int:
    """Return absolute byte error for value -> byte -> value round trip."""
    encoded = gene_value_to_byte(gene_value)
    decoded = byte_to_gene_value(encoded)
    re_encoded = gene_value_to_byte(decoded)
    return abs(encoded - re_encoded)
