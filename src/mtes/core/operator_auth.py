"""Operator authentication for evolution admin commands per SRS §7.4."""

import logging
import os
from dataclasses import dataclass, field

from mtes.shared.exceptions import MtesError

logger = logging.getLogger(__name__)

OPERATOR_TOKEN_ENV = "MTES_OPERATOR_TOKEN"
OPERATOR_ALLOW_LIST_ENV = "MTES_OPERATOR_ALLOW_LIST"


class OperatorAuthenticationError(MtesError):
    """Raised when an operator command lacks valid authentication."""


@dataclass
class OperatorAuthService:
    """Validate operator credentials from environment configuration."""

    allowed_operator_ids: frozenset[str] = field(default_factory=frozenset)
    operator_token: str | None = None

    @classmethod
    def from_environment(cls) -> "OperatorAuthService":
        token = os.environ.get(OPERATOR_TOKEN_ENV)
        allow_list_raw = os.environ.get(OPERATOR_ALLOW_LIST_ENV, "")
        allowed = frozenset(
            item.strip() for item in allow_list_raw.split(",") if item.strip()
        )
        return cls(allowed_operator_ids=allowed, operator_token=token)

    def authenticate(
        self,
        *,
        operator_id: str,
        presented_token: str | None,
    ) -> None:
        if not self.allowed_operator_ids:
            raise OperatorAuthenticationError("Operator allow-list is not configured")
        if operator_id not in self.allowed_operator_ids:
            raise OperatorAuthenticationError(f"Operator {operator_id} is not authorized")
        if not self.operator_token:
            raise OperatorAuthenticationError("Operator token is not configured")
        if presented_token != self.operator_token:
            raise OperatorAuthenticationError("Invalid operator token")

    def audit_admin_command(self, *, operator_id: str, command: str) -> None:
        logger.info(
            "operator_admin_command",
            extra={
                "operator_id": operator_id,
                "command": command,
                "module": "core.operator_auth",
                "operation": "admin_command",
            },
        )
