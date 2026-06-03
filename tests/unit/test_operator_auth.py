"""Operator authentication tests."""

import pytest

from mtes.core.operator_auth import OperatorAuthService, OperatorAuthenticationError


def test_unconfigured_allow_list_rejects() -> None:
    auth = OperatorAuthService(allowed_operator_ids=frozenset(), operator_token="token")
    with pytest.raises(OperatorAuthenticationError):
        auth.authenticate(operator_id="op", presented_token="token")


def test_invalid_token_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MTES_OPERATOR_TOKEN", "expected")
    monkeypatch.setenv("MTES_OPERATOR_ALLOW_LIST", "operator-1")
    auth = OperatorAuthService.from_environment()
    with pytest.raises(OperatorAuthenticationError):
        auth.authenticate(operator_id="operator-1", presented_token="wrong")
