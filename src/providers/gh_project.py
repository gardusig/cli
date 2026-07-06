"""GitHub Projects v2 providers (CLI subprocess and GraphQL)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Protocol

from src.providers.gh_transport import GhApiTransport, GhAutoTransport, GhCliTransport, GhTransportMode, make_gh_transport
from src.utils.external_client import ExternalClient
from src.utils.process import run_gh


class GhProjectProvider(Protocol):
    def run(self, args: Sequence[str], *, check: bool = True) -> str: ...

    def run_json(self, args: Sequence[str]) -> Any: ...


class GhProjectCliProvider:
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


def project_provider_uses_api(*, repo: str | None, transport: GhTransportMode) -> bool:
    if transport == "cli":
        return False
    if transport == "api":
        return True
    resolved = make_gh_transport(repo=repo, mode="auto")
    if isinstance(resolved, GhAutoTransport):
        return isinstance(resolved._transport, GhApiTransport)
    return isinstance(resolved, GhApiTransport)


def make_project_provider(
    *,
    repo: str | None = None,
    transport: GhTransportMode = "cli",
    graphql: Any | None = None,
) -> GhProjectProvider:
    if project_provider_uses_api(repo=repo, transport=transport):
        from src.providers.gh_project_graphql import GhProjectGraphqlProvider

        if graphql is None:
            resolved = make_gh_transport(repo=repo, mode=transport if transport != "auto" else "auto")
            if isinstance(resolved, GhAutoTransport):
                graphql = resolved._transport.graphql
            else:
                graphql = resolved.graphql
        return GhProjectGraphqlProvider(graphql)
    return GhProjectCliProvider()
