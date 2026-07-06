from __future__ import annotations

from unittest.mock import MagicMock

from src.providers.gh_project import make_project_provider, project_provider_uses_api
from src.providers.gh_project_graphql import GhProjectGraphqlProvider


def test_project_provider_uses_cli_by_default() -> None:
    assert project_provider_uses_api(repo="owner/repo", transport="cli") is False
    assert project_provider_uses_api(repo="owner/repo", transport="api") is True


def test_graphql_project_list() -> None:
    graphql = MagicMock(
        return_value={
            "data": {
                "user": {"projectsV2": {"nodes": [{"id": "PVT_1", "title": "Roadmap", "number": 1}]}},
                "organization": None,
            }
        }
    )
    provider = GhProjectGraphqlProvider(graphql)
    rows = provider.run_json(["list", "--owner", "owner", "--limit", "5", "--format", "json"])
    assert rows[0]["title"] == "Roadmap"


def test_graphql_project_create() -> None:
    graphql = MagicMock(
        side_effect=[
            {"data": {"user": {"id": "U_1"}, "organization": None}},
            {"data": {"createProjectV2": {"projectV2": {"id": "PVT_2", "title": "New", "number": 2}}}},
        ]
    )
    provider = GhProjectGraphqlProvider(graphql)
    payload = provider.run_json(["create", "--owner", "owner", "--title", "New", "--format", "json"])
    assert payload["number"] == 2


def test_make_project_provider_api() -> None:
    provider = make_project_provider(repo="owner/repo", transport="api", graphql=MagicMock())
    assert isinstance(provider, GhProjectGraphqlProvider)
