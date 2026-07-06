"""GitHub Projects v2 subprocess provider.

This provider intentionally does not use :class:`src.providers.gh.GhProvider`
because Projects v2 has a separate ``gh project`` command shape. Both
``cli gh project ...`` and top-level ``cli project ...`` use this reviewed
Projects surface with write gates.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from src.utils.external_client import ExternalClient
from src.utils.process import run_gh


class GhProjectProvider:
    """Thin wrapper around ``gh project`` commands."""

    def __init__(self) -> None:
        self._external = ExternalClient("gh")

    def run(self, args: Sequence[str], *, check: bool = True) -> str:
        full_args = ["project", *args]
        label = " ".join(full_args[:3])

        def _invoke() -> str:
            result = run_gh(full_args, check=check)
            return result.stdout.strip()

        return self._external.call(label, _invoke)

    def run_json(self, args: Sequence[str]) -> Any:
        text = self.run(args)
        if not text:
            return {}
        return json.loads(text)
