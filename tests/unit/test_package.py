"""Smoke tests for package scaffold."""

import mtes


def test_version_is_defined() -> None:
    assert mtes.__version__ == "0.1.0"
