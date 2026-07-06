"""GitHub transport implementations for CLI and API-backed `cli gh` commands."""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Sequence
from typing import Any, Literal, Protocol
from urllib.parse import quote

import httpx

from src.utils.config import default_config_dir, load_config
from src.utils.external_client import ExternalClient
from src.utils.http import default_http_timeout
from src.utils.process import GhCommandError, run_gh

GhTransportMode = Literal["cli", "api", "auto"]


class GhTransportError(RuntimeError):
    """Raised when no GitHub transport can satisfy the request."""


class GhTransport(Protocol):
    repo: str | None

    def run(self, args: Sequence[str], *, check: bool = True) -> str: ...

    def run_json(self, args: Sequence[str]) -> Any: ...

    def default_repo(self) -> str: ...

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]: ...


class GhCliTransport:
    """Current subprocess `gh` implementation."""

    def __init__(self, *, repo: str | None = None) -> None:
        self.repo = repo
        self._external = ExternalClient("gh")

    def _base_args(self) -> list[str]:
        if self.repo:
            return ["--repo", self.repo]
        return []

    def run(self, args: Sequence[str], *, check: bool = True) -> str:
        label = " ".join(args[:2]) if len(args) >= 2 else " ".join(args)

        def _invoke() -> str:
            result = run_gh([*self._base_args(), *args], check=check)
            return result.stdout.strip()

        return self._external.call(label, _invoke)

    def run_json(self, args: Sequence[str]) -> Any:
        text = self.run(args)
        if not text:
            return []
        return json.loads(text)

    def default_repo(self) -> str:
        data = self.run_json(["repo", "view", "--json", "nameWithOwner"])
        return str(data["nameWithOwner"])

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        args = ["api", "graphql", "-f", f"query={query}"]
        for key, value in (variables or {}).items():
            args.extend(["-F", f"{key}={value}"])
        data = self.run_json(args)
        return data if isinstance(data, dict) else {"data": data}

    def is_authenticated(self) -> bool:
        if shutil.which("gh") is None:
            return False
        result = run_gh(["auth", "status"], check=False)
        return result.returncode == 0


class GhApiTransport:
    """GitHub REST/GraphQL transport with gh-like argv adapters."""

    api_url = "https://api.github.com"

    def __init__(self, *, repo: str | None = None, token: str | None = None) -> None:
        self.repo = repo
        self.token = token or github_token()
        if not self.token:
            raise GhTransportError(
                "GitHub API transport needs GITHUB_TOKEN, GH_TOKEN, or auth.gh.token_file."
            )
        self._external = ExternalClient("github-api")

    def run(self, args: Sequence[str], *, check: bool = True) -> str:
        data = self._dispatch(list(args), check=check)
        if isinstance(data, str):
            return data
        return json.dumps(data)

    def run_json(self, args: Sequence[str]) -> Any:
        data = self._dispatch(list(args), check=True)
        if isinstance(data, str):
            if not data:
                return []
            return json.loads(data)
        return data

    def default_repo(self) -> str:
        if self.repo:
            return self.repo
        configured = load_config().gh.issues.repo.strip()
        if configured:
            return configured
        raise GhTransportError("API transport requires --repo owner/name or gh.issues.repo.")

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", "/graphql", json={"query": query, "variables": variables or {}})

    def _dispatch(self, args: list[str], *, check: bool) -> Any:
        if args[:2] == ["issue", "list"]:
            return self._issue_list(args)
        if args[:2] == ["issue", "view"]:
            return self._issue_view(args)
        if args[:2] == ["search", "issues"]:
            return self._issue_search(args)
        if args[:2] == ["issue", "create"]:
            return self._issue_create(args)
        if args[:2] == ["issue", "edit"]:
            return self._issue_edit(args)
        if args[:2] == ["issue", "reopen"]:
            return self._issue_state(args, state="open")
        if args[:2] == ["issue", "delete"]:
            return self._issue_delete(args)
        if args[:2] == ["issue", "comment"]:
            return self._issue_comment(args)
        if args[:2] == ["label", "list"]:
            return self._label_list()
        if args[:2] == ["label", "create"]:
            return self._label_create(args)
        if args[:2] == ["label", "delete"]:
            return self._label_delete(args)
        if args[:2] == ["pr", "list"]:
            return self._pr_list(args)
        if args[:2] == ["pr", "view"]:
            return self._pr_view(args)
        if args[:2] == ["pr", "create"]:
            return self._pr_create(args)
        if args[:2] == ["pr", "edit"]:
            return self._pr_edit(args)
        if args[:2] == ["pr", "close"]:
            return self._pr_state(args, state="closed")
        if args[:2] == ["pr", "reopen"]:
            return self._pr_state(args, state="open")
        if args[:2] == ["pr", "comment"]:
            return self._pr_comment(args)
        if args[:2] == ["pr", "checks"]:
            return self._pr_checks(args)
        if args[:2] == ["pr", "review"]:
            return self._pr_review(args)
        if args[:2] == ["pr", "ready"]:
            return self._pr_ready(args)
        if args[:2] == ["repo", "view"]:
            return self._repo_view(args)
        if args[:2] == ["repo", "list"]:
            return self._repo_list(args)
        raise GhTransportError(f"API transport does not support gh argv: {' '.join(args)}")

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        def _invoke() -> Any:
            with httpx.Client(
                base_url=self.api_url,
                timeout=default_http_timeout(),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            ) as client:
                response = client.request(method, path, **kwargs)
                response.raise_for_status()
                if not response.content:
                    return {}
                return response.json()

        return self._external.call(f"github-api {method} {path}", _invoke)

    def _repo_path(self, suffix: str = "") -> str:
        repo = self.default_repo()
        return f"/repos/{repo}{suffix}"

    def _issue_list(self, args: list[str]) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"state": _option(args, "--state", "open"), "per_page": int(_option(args, "--limit", "30"))}
        labels = _options(args, "--label")
        if labels:
            params["labels"] = ",".join(labels)
        rows = self._request("GET", self._repo_path("/issues"), params=params)
        return [row for row in rows if "pull_request" not in row]

    def _issue_view(self, args: list[str]) -> dict[str, Any]:
        number = args[2]
        data = self._request("GET", self._repo_path(f"/issues/{number}"))
        if "--comments" in args:
            data["comments"] = self._request("GET", self._repo_path(f"/issues/{number}/comments"))
        return data

    def _issue_search(self, args: list[str]) -> list[dict[str, Any]]:
        query = args[2]
        limit = int(_option(args, "--limit", "30"))
        data = self._request("GET", "/search/issues", params={"q": query, "per_page": limit})
        return data.get("items", [])

    def _issue_create(self, args: list[str]) -> str:
        payload: dict[str, Any] = {"title": _required_option(args, "--title")}
        body_file = _option(args, "--body-file")
        body = open(body_file, encoding="utf-8").read() if body_file else _option(args, "--body")
        if body is not None:
            payload["body"] = body
        labels = _option(args, "--label")
        if labels:
            payload["labels"] = [part for part in labels.split(",") if part]
        data = self._request("POST", self._repo_path("/issues"), json=payload)
        return str(data.get("html_url", ""))

    def _issue_edit(self, args: list[str]) -> dict[str, Any]:
        number = args[2]
        payload: dict[str, Any] = {}
        if (title := _option(args, "--title")) is not None:
            payload["title"] = title
        body_file = _option(args, "--body-file")
        body = open(body_file, encoding="utf-8").read() if body_file else _option(args, "--body")
        if body is not None:
            payload["body"] = body
        data = self._request("PATCH", self._repo_path(f"/issues/{number}"), json=payload)
        for label in _options(args, "--add-label"):
            self._request("POST", self._repo_path(f"/issues/{number}/labels"), json={"labels": [label]})
        return data

    def _issue_state(self, args: list[str], *, state: str) -> dict[str, Any]:
        return self._request("PATCH", self._repo_path(f"/issues/{args[2]}"), json={"state": state})

    def _issue_delete(self, args: list[str]) -> dict[str, Any]:
        self._request("DELETE", self._repo_path(f"/issues/{args[2]}"))
        return {"number": int(args[2]), "deleted": True}

    def _issue_comment(self, args: list[str]) -> dict[str, Any]:
        return self._request("POST", self._repo_path(f"/issues/{args[2]}/comments"), json={"body": _required_option(args, "--body")})

    def _label_list(self) -> list[dict[str, Any]]:
        return self._request("GET", self._repo_path("/labels"), params={"per_page": 100})

    def _label_create(self, args: list[str]) -> dict[str, Any]:
        payload = {"name": args[2], "color": _option(args, "--color", "ededed"), "description": _option(args, "--description", "")}
        return self._request("POST", self._repo_path("/labels"), json=payload)

    def _label_delete(self, args: list[str]) -> dict[str, Any]:
        self._request("DELETE", self._repo_path(f"/labels/{quote(args[2], safe='')}"))
        return {"name": args[2], "deleted": True}

    def _pr_list(self, args: list[str]) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"state": _option(args, "--state", "open"), "per_page": int(_option(args, "--limit", "30"))}
        if (head := _option(args, "--head")) is not None:
            params["head"] = head
        if (base := _option(args, "--base")) is not None:
            params["base"] = base
        return self._request("GET", self._repo_path("/pulls"), params=params)

    def _pr_view(self, args: list[str]) -> dict[str, Any]:
        return self._request("GET", self._repo_path(f"/pulls/{args[2]}"))

    def _pr_create(self, args: list[str]) -> str:
        payload = {
            "title": _required_option(args, "--title"),
            "head": _option(args, "--head") or self._default_head(),
            "base": _option(args, "--base", "main"),
            "body": open(_option(args, "--body-file"), encoding="utf-8").read()
            if _option(args, "--body-file")
            else _option(args, "--body", ""),
        }
        data = self._request("POST", self._repo_path("/pulls"), json=payload)
        return str(data.get("html_url", ""))

    def _pr_edit(self, args: list[str]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if (title := _option(args, "--title")) is not None:
            payload["title"] = title
        body_file = _option(args, "--body-file")
        body = open(body_file, encoding="utf-8").read() if body_file else _option(args, "--body")
        if body is not None:
            payload["body"] = body
        return self._request("PATCH", self._repo_path(f"/pulls/{args[2]}"), json=payload)

    def _pr_state(self, args: list[str], *, state: str) -> dict[str, Any]:
        return self._request("PATCH", self._repo_path(f"/pulls/{args[2]}"), json={"state": state})

    def _pr_comment(self, args: list[str]) -> dict[str, Any]:
        return self._request("POST", self._repo_path(f"/issues/{args[2]}/comments"), json={"body": _required_option(args, "--body")})

    def _pr_checks(self, args: list[str]) -> list[dict[str, Any]]:
        pr = self._pr_view(args)
        sha = pr.get("head", {}).get("sha") or pr.get("headRefOid")
        if not sha:
            return []
        data = self._request("GET", self._repo_path(f"/commits/{sha}/check-runs"), params={"per_page": 100})
        return data.get("check_runs", [])

    def _pr_review(self, args: list[str]) -> dict[str, Any]:
        event = "COMMENT"
        if "--approve" in args:
            event = "APPROVE"
        elif "--request-changes" in args:
            event = "REQUEST_CHANGES"
        payload = {"event": event, "body": _option(args, "--body", "")}
        return self._request("POST", self._repo_path(f"/pulls/{args[2]}/reviews"), json=payload)

    def _pr_ready(self, args: list[str]) -> dict[str, Any]:
        query = "mutation($id:ID!){markPullRequestReadyForReview(input:{pullRequestId:$id}){pullRequest{id number isDraft}}}"
        pr = self._pr_view(args)
        node_id = pr.get("node_id") or pr.get("id")
        return self.graphql(query, {"id": node_id})

    def _repo_view(self, args: list[str]) -> dict[str, Any]:
        fields = (_option(args, "--json", "nameWithOwner") or "nameWithOwner").split(",")
        repo = self.default_repo()
        data = self._request("GET", self._repo_path())
        payload: dict[str, Any] = {}
        for field in fields:
            if field == "nameWithOwner":
                payload[field] = repo
            elif field == "owner":
                payload[field] = data.get("owner")
            elif field in {"issueTemplates", "pullRequestTemplates"}:
                payload[field] = []
            else:
                payload[field] = data.get(field)
        return payload

    def _repo_list(self, args: list[str]) -> list[dict[str, Any]]:
        owner = _required_option(args, "--owner")
        limit = int(_option(args, "--limit", "100"))
        return self._request("GET", f"/users/{owner}/repos", params={"per_page": limit})

    def _default_head(self) -> str:
        return os.environ.get("CLI_GH_HEAD", "HEAD")


class GhAutoTransport:
    """Auto-select CLI transport first, then API token fallback."""

    def __init__(self, *, repo: str | None = None) -> None:
        self.repo = repo
        cli = GhCliTransport(repo=repo)
        if cli.is_authenticated():
            self._transport: GhTransport = cli
        else:
            self._transport = GhApiTransport(repo=repo)

    def run(self, args: Sequence[str], *, check: bool = True) -> str:
        return self._transport.run(args, check=check)

    def run_json(self, args: Sequence[str]) -> Any:
        return self._transport.run_json(args)

    def default_repo(self) -> str:
        return self._transport.default_repo()

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._transport.graphql(query, variables)


def github_token() -> str | None:
    for env_name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    raw_file = load_config().auth.gh.token_file.strip()
    if not raw_file:
        return None
    path = os.path.expanduser(raw_file)
    if not os.path.isabs(path):
        path = str(default_config_dir() / path)
    try:
        token = open(path, encoding="utf-8").read().strip()
    except OSError:
        return None
    return token or None


def make_gh_transport(*, repo: str | None = None, mode: GhTransportMode = "cli") -> GhTransport:
    if mode == "cli":
        return GhCliTransport(repo=repo)
    if mode == "api":
        return GhApiTransport(repo=repo)
    if mode == "auto":
        try:
            return GhAutoTransport(repo=repo)
        except GhTransportError as exc:
            raise GhTransportError(
                "GitHub access unavailable: install/authenticate `gh` or set GITHUB_TOKEN/GH_TOKEN."
            ) from exc
    raise ValueError(f"Unknown GitHub transport: {mode}")


def _option(args: list[str], name: str, default: str | None = None) -> str | None:
    if name not in args:
        return default
    idx = args.index(name)
    if idx + 1 >= len(args):
        return default
    return args[idx + 1]


def _required_option(args: list[str], name: str) -> str:
    value = _option(args, name)
    if value is None:
        raise GhTransportError(f"Missing required option for API transport: {name}")
    return value


def _options(args: list[str], name: str) -> list[str]:
    values: list[str] = []
    for idx, arg in enumerate(args):
        if arg == name and idx + 1 < len(args):
            values.append(args[idx + 1])
    return values
