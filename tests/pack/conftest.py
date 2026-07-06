"""Pack test markers — doc contracts need docs/ (stripped from Docker unit context)."""

from __future__ import annotations

import pytest


def requires_docs(func):  # noqa: ANN001, ANN201
    return pytest.mark.requires_docs(pytest.mark.integration(func))
