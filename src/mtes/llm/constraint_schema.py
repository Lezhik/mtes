"""P3 constraint expansion schema validation."""

from typing import Any

from mtes.shared.exceptions import ConstraintViolationError

ALLOWED_CONSTRAINT_TYPES = frozenset({"required", "prohibited", "target"})


def validate_constraint_expansion_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate P3 output schema per LLM Interaction Specification §7.3."""
    constraints = payload.get("generation_constraints")
    if not isinstance(constraints, list) or not constraints:
        raise ConstraintViolationError("generation_constraints must be a non-empty list")

    for index, constraint in enumerate(constraints):
        if not isinstance(constraint, dict):
            raise ConstraintViolationError(f"constraint[{index}] must be an object")
        constraint_type = constraint.get("type")
        dimension = constraint.get("dimension")
        value = constraint.get("value")
        if constraint_type not in ALLOWED_CONSTRAINT_TYPES:
            raise ConstraintViolationError(f"constraint[{index}] has invalid type")
        if not isinstance(dimension, str) or not dimension.strip():
            raise ConstraintViolationError(f"constraint[{index}] missing dimension")
        if value is None:
            raise ConstraintViolationError(f"constraint[{index}] missing value")
    return payload
