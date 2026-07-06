"""GitHub CLI (`gh`) subprocess provider."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from src.providers.gh_transport import GhTransport, GhTransportMode, make_gh_transport
from src.services.gh_policy import check_gh_args
from src.utils.external_client import ExternalClient
from src.utils.process import run_gh


class GhProvider:
    """Thin wrapper around `gh` with optional --repo injection."""

    def __init__(
        self,
        *,
        repo: str | None = None,
        transport: GhTransportMode = "cli",
        transport_impl: GhTransport | None = None,
    ) -> None:
        self.repo = repo
        self.transport_mode = transport
        self._transport = transport_impl
        self._external = ExternalClient("gh")

    def _base_args(self) -> list[str]:
        if self.repo:
            return ["--repo", self.repo]
        return []

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = True,
    ) -> str:
        check_gh_args(args)
        if self._transport is not None:
            return self._transport.run(args, check=check)
        if self.transport_mode != "cli":
            self._transport = make_gh_transport(repo=self.repo, mode=self.transport_mode)
            return self._transport.run(args, check=check)
        label = " ".join(args[:2]) if len(args) >= 2 else " ".join(args)

        def _invoke() -> str:
            result = run_gh([*self._base_args(), *args], check=check)
            return result.stdout.strip()

        return self._external.call(label, _invoke)

    def run_json(self, args: Sequence[str]) -> Any:
        if self._transport is not None or self.transport_mode != "cli":
            text_or_data = self.run(args)
            if not text_or_data:
                return []
            if isinstance(text_or_data, str):
                return json.loads(text_or_data)
            return text_or_data
        text = self.run(args)
        if not text:
            return []
        return json.loads(text)

    def default_repo(self) -> str:
        if self._transport is not None or self.transport_mode != "cli":
            if self._transport is None:
                self._transport = make_gh_transport(repo=self.repo, mode=self.transport_mode)
            return self._transport.default_repo()
        data = self.run_json(["repo", "view", "--json", "nameWithOwner"])
        return str(data["nameWithOwner"])

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._transport is None:
            self._transport = make_gh_transport(repo=self.repo, mode=self.transport_mode)
        return self._transport.graphql(query, variables)
