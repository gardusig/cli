"""GitHub Projects v2 GraphQL provider for API transport."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

GraphqlFn = Callable[[str, dict[str, Any] | None], dict[str, Any]]


class GhProjectGraphqlProvider:
    """GraphQL-backed implementation of ``gh project`` argv shapes."""

    def __init__(self, graphql: GraphqlFn) -> None:
        self._graphql = graphql

    def run(self, args: list[str] | tuple[str, ...], *, check: bool = True) -> str:
        data = self.run_json(list(args))
        if isinstance(data, str):
            return data
        return json.dumps(data)

    def run_json(self, args: list[str]) -> Any:
        cmd = _strip_format(list(args))
        if not cmd:
            raise RuntimeError("empty gh project argv")
        if cmd[0] == "list":
            return self._project_list(cmd)
        if cmd[0] == "view":
            return self._project_view(cmd)
        if cmd[0] == "create":
            return self._project_create(cmd)
        if cmd[0] == "edit":
            return self._project_edit(cmd)
        if cmd[0] == "delete":
            return self._project_delete(cmd)
        if cmd[0] == "field-list":
            return self._field_list(cmd)
        if cmd[0] == "item-list":
            return self._item_list(cmd)
        if cmd[0] == "item-add":
            return self._item_add(cmd)
        if cmd[0] == "item-edit":
            return self._item_edit(cmd)
        if cmd[0] == "item-delete":
            return self._item_delete(cmd)
        if cmd[0] == "item-archive":
            return self._item_archive(cmd)
        raise RuntimeError(f"GraphQL project provider does not support argv: {' '.join(cmd)}")

    def _project_list(self, args: list[str]) -> list[dict[str, Any]]:
        owner = _required(args, "--owner")
        limit = int(_option(args, "--limit", "30"))
        query = """
        query($owner:String!, $first:Int!) {
          user(login: $owner) {
            projectsV2(first: $first) { nodes { id title number url } }
          }
          organization(login: $owner) {
            projectsV2(first: $first) { nodes { id title number url } }
          }
        }
        """
        data = _data_root(self._graphql(query, {"owner": owner, "first": limit}))
        user_rows = ((data.get("user") or {}).get("projectsV2") or {}).get("nodes") or []
        org_rows = ((data.get("organization") or {}).get("projectsV2") or {}).get("nodes") or []
        rows = [row for row in [*user_rows, *org_rows] if isinstance(row, dict)]
        return rows[:limit]

    def _project_view(self, args: list[str]) -> dict[str, Any]:
        owner = _required(args, "--owner")
        number = int(args[1])
        return self._project_by_number(owner, number)

    def _project_create(self, args: list[str]) -> dict[str, Any]:
        owner = _required(args, "--owner")
        title = _required(args, "--title")
        owner_id = self._owner_id(owner)
        query = """
        mutation($ownerId:ID!, $title:String!) {
          createProjectV2(input: {ownerId: $ownerId, title: $title}) {
            projectV2 { id title number url }
          }
        }
        """
        data = _data_root(self._graphql(query, {"ownerId": owner_id, "title": title}))
        project = (data.get("createProjectV2") or {}).get("projectV2")
        if not isinstance(project, dict):
            raise RuntimeError("createProjectV2 returned no project")
        return project

    def _project_edit(self, args: list[str]) -> dict[str, Any]:
        owner = _required(args, "--owner")
        number = int(args[1])
        project = self._project_by_number(owner, number)
        project_id = str(project["id"])
        title = _option(args, "--title")
        readme = _option(args, "--readme")
        short_description = readme if readme is not None else None
        query = """
        mutation($id:ID!, $title:String, $shortDescription:String) {
          updateProjectV2(input: {projectId: $id, title: $title, shortDescription: $shortDescription}) {
            projectV2 { id title number url }
          }
        }
        """
        data = _data_root(
            self._graphql(
                query,
                {"id": project_id, "title": title, "shortDescription": short_description},
            )
        )
        updated = (data.get("updateProjectV2") or {}).get("projectV2")
        return updated if isinstance(updated, dict) else project

    def _project_delete(self, args: list[str]) -> dict[str, Any]:
        owner = _required(args, "--owner")
        number = int(args[1])
        project = self._project_by_number(owner, number)
        query = "mutation($id:ID!){deleteProjectV2(input:{projectId:$id}){projectV2{id number}}}"
        _data_root(self._graphql(query, {"id": project["id"]}))
        return {"number": number, "owner": owner, "deleted": True}

    def _field_list(self, args: list[str]) -> list[dict[str, Any]]:
        owner = _required(args, "--owner")
        number = int(args[1])
        project_id = self._project_by_number(owner, number)["id"]
        query = """
        query($id:ID!) {
          node(id: $id) {
            ... on ProjectV2 {
              fields(first: 50) {
                nodes {
                  ... on ProjectV2FieldCommon { id name }
                  ... on ProjectV2SingleSelectField { id name options { id name } }
                }
              }
            }
          }
        }
        """
        data = _data_root(self._graphql(query, {"id": project_id}))
        node = data.get("node") if isinstance(data.get("node"), dict) else {}
        fields = (node.get("fields") or {}).get("nodes") or []
        return [row for row in fields if isinstance(row, dict)]

    def _item_list(self, args: list[str]) -> list[dict[str, Any]]:
        owner = _required(args, "--owner")
        number = int(args[1])
        limit = int(_option(args, "--limit", "100"))
        project_id = self._project_by_number(owner, number)["id"]
        query = """
        query($id:ID!, $first:Int!) {
          node(id: $id) {
            ... on ProjectV2 {
              items(first: $first) {
                nodes {
                  id
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field { ... on ProjectV2SingleSelectField { name } }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field { ... on ProjectV2FieldCommon { name } }
                      }
                    }
                  }
                  content {
                    __typename
                    ... on Issue { number title url state }
                    ... on PullRequest { number title url state }
                  }
                }
              }
            }
          }
        }
        """
        data = _data_root(self._graphql(query, {"id": project_id, "first": limit}))
        node = data.get("node") if isinstance(data.get("node"), dict) else {}
        items = (node.get("items") or {}).get("nodes") or []
        out: list[dict[str, Any]] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            item = dict(row)
            content = item.get("content")
            if isinstance(content, dict):
                ctype = str(content.get("__typename") or "")
                if ctype == "Issue":
                    content["type"] = "Issue"
                elif ctype == "PullRequest":
                    content["type"] = "PullRequest"
                item["content"] = content
            out.append(item)
        return out

    def _item_add(self, args: list[str]) -> dict[str, Any]:
        owner = _required(args, "--owner")
        number = int(args[1])
        url = _required(args, "--url")
        project_id = self._project_by_number(owner, number)["id"]
        content_id = self._content_id_for_url(url)
        query = """
        mutation($projectId:ID!, $contentId:ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """
        data = _data_root(self._graphql(query, {"projectId": project_id, "contentId": content_id}))
        item = (data.get("addProjectV2ItemById") or {}).get("item")
        if not isinstance(item, dict):
            raise RuntimeError("addProjectV2ItemById returned no item")
        return {"id": item.get("id"), "item": item, "url": url}

    def _item_edit(self, args: list[str]) -> dict[str, Any]:
        item_id = _required(args, "--id")
        field_id = _required(args, "--field-id")
        if (option_id := _option(args, "--single-select-option-id")) is not None:
            value = {"singleSelectOptionId": option_id}
        elif (date_val := _option(args, "--date")) is not None:
            value = {"date": date_val}
        else:
            value = {"text": _option(args, "--text", "")}
        query = """
        mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $value:ProjectV2FieldValue!) {
          updateProjectV2ItemFieldValue(
            input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value}
          ) { projectV2Item { id } }
        }
        """
        project_id = _required(args, "--project-id")
        data = _data_root(
            self._graphql(
                query,
                {
                    "projectId": project_id,
                    "itemId": item_id,
                    "fieldId": field_id,
                    "value": value,
                },
            )
        )
        item = (data.get("updateProjectV2ItemFieldValue") or {}).get("projectV2Item")
        return item if isinstance(item, dict) else {"id": item_id, "field": field_id, "value": value}

    def _item_delete(self, args: list[str]) -> dict[str, Any]:
        item_id = _required(args, "--id")
        project_id = _required(args, "--project-id")
        query = "mutation($projectId:ID!, $itemId:ID!){deleteProjectV2Item(input:{projectId:$projectId, itemId:$itemId}){deletedItemId}}"
        data = _data_root(self._graphql(query, {"projectId": project_id, "itemId": item_id}))
        deleted = (data.get("deleteProjectV2Item") or {}).get("deletedItemId")
        return {"id": deleted or item_id, "action": "deleted"}

    def _item_archive(self, args: list[str]) -> dict[str, Any]:
        item_id = _required(args, "--id")
        return {"id": item_id, "action": "archived"}

    def _project_by_number(self, owner: str, number: int) -> dict[str, Any]:
        query = """
        query($owner:String!, $number:Int!) {
          user(login: $owner) {
            projectV2(number: $number) { id title number url }
          }
          organization(login: $owner) {
            projectV2(number: $number) { id title number url }
          }
        }
        """
        data = _data_root(self._graphql(query, {"owner": owner, "number": number}))
        user_project = (data.get("user") or {}).get("projectV2")
        org_project = (data.get("organization") or {}).get("projectV2")
        project = user_project or org_project
        if not isinstance(project, dict):
            raise RuntimeError(f"Project not found via GraphQL: {owner}/{number}")
        return project

    def _owner_id(self, owner: str) -> str:
        query = """
        query($owner:String!) {
          user(login: $owner) { id }
          organization(login: $owner) { id }
        }
        """
        data = _data_root(self._graphql(query, {"owner": owner}))
        user_id = (data.get("user") or {}).get("id")
        org_id = (data.get("organization") or {}).get("id")
        owner_id = user_id or org_id
        if not owner_id:
            raise RuntimeError(f"Owner not found: {owner}")
        return str(owner_id)

    def _content_id_for_url(self, url: str) -> str:
        query = """
        query($url:URI!) {
          resource(url: $url) {
            ... on Issue { id }
            ... on PullRequest { id }
          }
        }
        """
        data = _data_root(self._graphql(query, {"url": url}))
        resource = data.get("resource")
        if not isinstance(resource, dict) or not resource.get("id"):
            raise RuntimeError(f"Could not resolve GitHub node id for url: {url}")
        return str(resource["id"])


def _data_root(payload: dict[str, Any]) -> dict[str, Any]:
    root = payload.get("data", payload)
    return root if isinstance(root, dict) else {}


def _strip_format(args: list[str]) -> list[str]:
    out = list(args)
    while "--format" in out:
        idx = out.index("--format")
        del out[idx : idx + 2]
    return out


def _option(args: list[str], name: str, default: str | None = None) -> str | None:
    if name not in args:
        return default
    idx = args.index(name)
    if idx + 1 >= len(args):
        return default
    return args[idx + 1]


def _required(args: list[str], name: str) -> str:
    value = _option(args, name)
    if value is None:
        raise RuntimeError(f"Missing required gh project arg: {name}")
    return value
