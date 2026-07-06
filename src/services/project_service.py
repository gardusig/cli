"""GitHub Projects v2 service and local project-pair workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from src.providers.gh_project import GhProjectProvider
from src.services.gh_service import GhService
from src.services.notion_pairs import build_from_disk, combine_task, load_pairs, save_pairs, slugify
from src.utils.config import ProjectConfig, load_config, project_pairs_file, project_task_root


@dataclass(frozen=True)
class ProjectRef:
    owner: str
    number: int | None = None
    project_id: str = ""

    def require_number(self) -> int:
        if self.number is None:
            raise RuntimeError("Project number is required for this gh project command.")
        return self.number


@dataclass(frozen=True)
class ProjectPairStatus:
    enabled: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    broken: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "disabled": self.disabled,
            "broken": self.broken,
            "counts": {
                "enabled": len(self.enabled),
                "disabled": len(self.disabled),
                "broken": len(self.broken),
            },
        }


def _label_names(labels: object) -> list[str]:
    if not isinstance(labels, list):
        return []
    names: list[str] = []
    for label in labels:
        if isinstance(label, dict):
            value = label.get("name")
        else:
            value = label
        if value:
            names.append(str(value))
    return names


def _normalize_items(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "nodes"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def _normalize_fields(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("fields", "nodes"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def _content_number(item: dict[str, Any], kind: str | None = None) -> int | None:
    content = item.get("content") if isinstance(item.get("content"), dict) else item
    number = content.get("number") if isinstance(content, dict) else None
    if number is None:
        return None
    if kind:
        content_type = str(content.get("type", content.get("__typename", ""))).lower()
        if content_type and kind.lower() not in content_type:
            return None
    return int(number)


def _item_id(item: dict[str, Any]) -> str:
    value = item.get("id") or item.get("item_id")
    if not value:
        raise RuntimeError(f"Project item missing id: {item}")
    return str(value)


def _field_value_rows(item: dict[str, Any]) -> list[dict[str, Any]]:
    raw = item.get("fieldValues") or item.get("field_values") or item.get("fields") or []
    if isinstance(raw, dict):
        return [row for row in raw.values() if isinstance(row, dict)]
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]
    return []


def _read_item_runtime_fields(
    item: dict[str, Any],
    *,
    config: ProjectConfig,
    issue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract board runtime fields for ingest → header yaml."""
    out: dict[str, Any] = {}
    status_field = config.fields.status.lower()
    deadline_field = config.fields.deadline.lower()

    if item.get("status"):
        out["forced_status"] = str(item["status"])

    for row in _field_value_rows(item):
        field = row.get("field") if isinstance(row.get("field"), dict) else {}
        field_name = str(field.get("name") or "").lower()
        if not field_name:
            continue
        if field_name == status_field or field_name == "status":
            option_name = row.get("name")
            if isinstance(row.get("option"), dict):
                option_name = row["option"].get("name") or option_name
            if option_name:
                out["forced_status"] = str(option_name)
        elif field_name == deadline_field or field_name == "deadline":
            date_val = row.get("date") or row.get("value") or row.get("name")
            if isinstance(date_val, dict):
                date_val = date_val.get("start") or date_val.get("date")
            if date_val:
                out["deadline"] = str(date_val)

    if issue:
        labels = _label_names(issue.get("labels"))
        if labels:
            out["labels"] = labels
    return out


class ProjectService:
    def __init__(
        self,
        *,
        provider: GhProjectProvider | None = None,
        gh_service: GhService | None = None,
        config: ProjectConfig | None = None,
        repo: str | None = None,
    ) -> None:
        self.provider = provider or GhProjectProvider()
        self.gh = gh_service or GhService(repo=repo)
        self.config = config or load_config().project

    def snapshot_summary(self, ref: ProjectRef | None = None) -> list[str]:
        ref = ref or self.default_ref()
        return [
            f"owner: {ref.owner}",
            f"project: {ref.number if ref.number is not None else ref.project_id}",
        ]

    def default_ref(self) -> ProjectRef:
        default = self.config.default
        owner = default.owner.strip() or self.config.owner.strip()
        number = default.number if default.number is not None else self.config.number
        project_id = default.project_id.strip() or self.config.project_id.strip()
        if not owner:
            raise RuntimeError("project.default.owner is not configured.")
        if number is None and not project_id:
            raise RuntimeError("project.default.number or project.default.project_id is not configured.")
        return ProjectRef(owner=owner, number=number, project_id=project_id)

    def ref(
        self,
        *,
        owner: str | None = None,
        number: int | None = None,
        project_id: str | None = None,
    ) -> ProjectRef:
        default = self.default_ref()
        return ProjectRef(
            owner=(owner or default.owner).strip(),
            number=number if number is not None else default.number,
            project_id=(project_id or default.project_id).strip(),
        )

    def project_list(self, *, owner: str, limit: int = 30) -> object:
        return self.provider.run_json(["list", "--owner", owner, "--limit", str(limit), "--format", "json"])

    def project_view(self, number: int, *, owner: str) -> object:
        return self.provider.run_json(["view", str(number), "--owner", owner, "--format", "json"])

    def project_create(
        self,
        *,
        owner: str,
        title: str,
    ) -> object:
        return self.provider.run_json(["create", "--owner", owner, "--title", title, "--format", "json"])

    def project_edit(
        self,
        number: int,
        *,
        owner: str,
        title: str | None = None,
        readme: str | None = None,
        visibility: str | None = None,
    ) -> object:
        args = ["edit", str(number), "--owner", owner]
        if title:
            args.extend(["--title", title])
        if readme:
            args.extend(["--readme", readme])
        if visibility:
            args.extend(["--visibility", visibility])
        args.extend(["--format", "json"])
        return self.provider.run_json(args)

    def project_delete(self, number: int, *, owner: str) -> object:
        return self.provider.run_json(["delete", str(number), "--owner", owner, "--format", "json"])

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run a GitHub GraphQL query through the shared gh/API transport."""
        return self.gh.provider.graphql(query, variables)

    def project_node(self, ref: ProjectRef) -> dict[str, Any]:
        """Resolve a Project v2 node through GraphQL for transport-shared callers."""
        query = """
        query($owner:String!, $number:Int!) {
          user(login: $owner) {
            projectV2(number: $number) {
              id
              title
              number
              url
            }
          }
          organization(login: $owner) {
            projectV2(number: $number) {
              id
              title
              number
              url
            }
          }
        }
        """
        data = self.graphql(query, {"owner": ref.owner, "number": ref.require_number()})
        root = data.get("data", data)
        user_project = (root.get("user") or {}).get("projectV2") if isinstance(root, dict) else None
        org_project = (root.get("organization") or {}).get("projectV2") if isinstance(root, dict) else None
        project = user_project or org_project
        if not isinstance(project, dict):
            raise RuntimeError(f"Project not found via GraphQL: {ref.owner}/{ref.require_number()}")
        return project

    def field_list(self, ref: ProjectRef) -> list[dict[str, Any]]:
        payload = self.provider.run_json(
            ["field-list", str(ref.require_number()), "--owner", ref.owner, "--format", "json"]
        )
        return _normalize_fields(payload)

    def item_list(self, ref: ProjectRef, *, limit: int = 100) -> list[dict[str, Any]]:
        payload = self.provider.run_json(
            [
                "item-list",
                str(ref.require_number()),
                "--owner",
                ref.owner,
                "--limit",
                str(limit),
                "--format",
                "json",
            ]
        )
        return _normalize_items(payload)

    def item_view(self, item_id: str, ref: ProjectRef | None = None) -> dict[str, Any]:
        ref = ref or self.default_ref()
        for item in self.item_list(ref):
            if str(item.get("id")) == item_id:
                return item
        raise RuntimeError(f"Project item not found: {item_id}")

    def item_add_url(self, url: str, ref: ProjectRef) -> dict[str, Any]:
        payload = self.provider.run_json(
            ["item-add", str(ref.require_number()), "--owner", ref.owner, "--url", url, "--format", "json"]
        )
        return payload if isinstance(payload, dict) else {"item": payload}

    def item_add_issue(self, issue_number: int, ref: ProjectRef) -> dict[str, Any]:
        issue = self.gh.issue_view(issue_number)
        url = str(issue.get("url") or "")
        if not url:
            raise RuntimeError(f"Issue #{issue_number} has no URL in gh response.")
        return self.item_add_url(url, ref)

    def item_add_pr(self, pr_number: int, ref: ProjectRef) -> dict[str, Any]:
        pr = self.gh.pr_view(pr_number)
        url = str(pr.get("url") or "")
        if not url:
            raise RuntimeError(f"PR #{pr_number} has no URL in gh response.")
        return self.item_add_url(url, ref)

    def find_item(
        self,
        ref: ProjectRef,
        *,
        item_id: str | None = None,
        issue: int | None = None,
        pr: int | None = None,
    ) -> dict[str, Any]:
        if item_id:
            return self.item_view(item_id, ref)
        kind = "issue" if issue is not None else "pullrequest"
        number = issue if issue is not None else pr
        if number is None:
            raise RuntimeError("Provide --id, --issue, or --pr.")
        for item in self.item_list(ref):
            if _content_number(item, kind) == number:
                return item
        raise RuntimeError(f"Project item not found for {kind} #{number}.")

    def resolve_field(self, ref: ProjectRef, field_name: str) -> dict[str, Any]:
        for field_row in self.field_list(ref):
            if str(field_row.get("name", "")).lower() == field_name.lower():
                return field_row
        raise RuntimeError(f"Project field not found: {field_name}")

    def resolve_option_id(self, field_row: dict[str, Any], option_label: str) -> str:
        options = field_row.get("options") or []
        if not isinstance(options, list):
            options = []
        for option in options:
            if not isinstance(option, dict):
                continue
            if str(option.get("name", "")).lower() == option_label.lower():
                option_id = option.get("id")
                if option_id:
                    return str(option_id)
        available = ", ".join(str(o.get("name")) for o in options if isinstance(o, dict))
        raise RuntimeError(f"Unknown project option {option_label!r}. Available: {available}")

    def resolve_lane(self, alias_or_label: str) -> str:
        value = alias_or_label.strip()
        if not value:
            raise RuntimeError("Project lane must not be blank.")
        if value in self.config.lanes:
            return self.config.lanes[value]
        lowered = value.lower()
        for alias, label in self.config.lanes.items():
            if alias.lower() == lowered:
                return label
        return value

    def item_set(
        self,
        ref: ProjectRef,
        *,
        item_id: str,
        field: str,
        value: str,
        value_kind: str = "text",
    ) -> dict[str, Any]:
        field_row = self.resolve_field(ref, field)
        args = [
            "item-edit",
            "--project-id",
            ref.project_id or str(ref.require_number()),
            "--id",
            item_id,
            "--field-id",
            str(field_row.get("id")),
        ]
        if value_kind == "single-select":
            args.extend(["--single-select-option-id", self.resolve_option_id(field_row, value)])
        elif value_kind == "date":
            args.extend(["--date", value])
        else:
            args.extend(["--text", value])
        return self.provider.run_json([*args, "--format", "json"])

    def item_status(self, ref: ProjectRef, *, item_id: str, status: str) -> dict[str, Any]:
        label = self.resolve_lane(status)
        return self.item_set(
            ref,
            item_id=item_id,
            field=self.config.fields.status,
            value=label,
            value_kind="single-select",
        )

    def item_archive(self, ref: ProjectRef, *, item_id: str) -> dict[str, Any]:
        self.provider.run(["item-archive", str(ref.require_number()), "--owner", ref.owner, "--id", item_id])
        return {"id": item_id, "action": "archived"}

    def item_delete(self, ref: ProjectRef, *, item_id: str) -> dict[str, Any]:
        self.provider.run(["item-delete", "--project-id", ref.project_id or str(ref.require_number()), "--id", item_id])
        return {"id": item_id, "action": "deleted"}

    def spawn(self, manifest_path: Path, *, dry_run: bool = False) -> dict[str, Any]:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected mapping in {manifest_path}")
        ref = self.ref(owner=data.get("owner"), number=data.get("project"), project_id=data.get("project_id"))
        default_status = str(data.get("status") or data.get("lane") or "")
        results: list[dict[str, Any]] = []
        for row in data.get("items") or []:
            if not isinstance(row, dict):
                raise ValueError("Each spawn item must be a mapping.")
            title = str(row["title"])
            body = str(row.get("body") or "")
            body_file = Path(row["body_file"]) if row.get("body_file") else None
            if body_file and not body_file.is_absolute():
                body_file = (manifest_path.parent / body_file).resolve()
            labels = [str(label) for label in row.get("labels") or []]
            status = str(row.get("status") or row.get("lane") or default_status)
            planned = {"title": title, "labels": labels, "status": status, "action": "planned"}
            if dry_run:
                results.append(planned)
                continue
            issue = self.gh.issue_create(title=title, body=body or None, body_file=body_file, labels=labels)
            added = self.item_add_url(str(issue["url"]), ref)
            item_id = str(added.get("id") or added.get("item", {}).get("id") or added.get("item_id") or "")
            if status and item_id:
                self.item_status(ref, item_id=item_id, status=status)
            results.append({**issue, "item_id": item_id, "status": status, "action": "created"})
        return {"project": ref.__dict__, "items": results, "dry_run": dry_run}

    def build_pairs_manifest(self, *, root: Path | None = None, manifest: Path | None = None) -> dict[str, Any]:
        root = root or project_task_root()
        manifest = manifest or project_pairs_file()
        pairs = build_from_disk(root)
        save_pairs(manifest, pairs)
        return {"processed": len(pairs), "manifest": str(manifest), "task_root": str(root)}

    def pairs_status(self, *, root: Path | None = None, manifest: Path | None = None) -> ProjectPairStatus:
        root = root or project_task_root()
        manifest = manifest or project_pairs_file()
        pairs = load_pairs(manifest, task_root=root)
        status = ProjectPairStatus()
        for pair in pairs:
            try:
                resolved = combine_task(pair, root)
                meta = resolved.metadata
                if not meta.enabled:
                    status.disabled.append(meta.name)
                    continue
                self._validate_pair_metadata(meta.model_dump())
                status.enabled.append(meta.name)
            except Exception as exc:
                status.broken.append(f"{pair.header_filepath} ({exc})")
        return status

    def _pair_deploy_priority(self, meta: dict[str, Any]) -> int:
        return 0 if self._is_maintenance(meta) else 1

    def _sorted_deploy_pairs(self, manifest: Path, *, root: Path) -> list:
        pairs = load_pairs(manifest, task_root=root)

        def sort_key(pair):
            try:
                raw = yaml.safe_load(pair.header_path(root).read_text(encoding="utf-8")) or {}
                meta = raw if isinstance(raw, dict) else {}
                return (self._pair_deploy_priority(meta), str(meta.get("name") or pair.header_filepath))
            except Exception:
                return (2, pair.header_filepath)

        return sorted(pairs, key=sort_key)

    def deploy_pairs(
        self,
        *,
        root: Path | None = None,
        manifest: Path | None = None,
        ref: ProjectRef | None = None,
    ) -> dict[str, Any]:
        root = root or project_task_root()
        manifest = manifest or project_pairs_file()
        ref = ref or self.default_ref()
        results: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []
        for pair in self._sorted_deploy_pairs(manifest, root=root):
            try:
                resolved = combine_task(pair, root)
                raw = yaml.safe_load(pair.header_path(root).read_text(encoding="utf-8")) or {}
                meta = {**resolved.metadata.model_dump(), **(raw if isinstance(raw, dict) else {})}
                name = str(meta.get("name") or pair.header_filepath)
                if not meta.get("enabled", True):
                    results.append({"name": name, "action": "skipped", "reason": "disabled"})
                    continue
                self._validate_pair_metadata(meta)
                labels = list(meta.get("labels") or [])
                tag = meta.get("tag")
                if tag and tag not in labels:
                    labels.append(str(tag))
                issue_number = meta.get("issue_number")
                if issue_number:
                    self.gh.issue_edit(
                        int(issue_number),
                        title=meta["name"],
                        body_file=pair.body_path(root),
                        add_labels=labels,
                    )
                    issue = self.gh.issue_view(int(issue_number))
                    action = "updated"
                else:
                    issue = self.gh.issue_create(
                        title=meta["name"],
                        body=resolved.body,
                        labels=labels,
                    )
                    action = "created"
                added = self.item_add_url(str(issue["url"]), ref)
                item_id = str(added.get("id") or added.get("item", {}).get("id") or added.get("item_id") or "")
                lane = str(meta.get("forced_status") or meta.get("status") or "")
                if lane and item_id:
                    self.item_status(ref, item_id=item_id, status=lane)
                deadline = meta.get("deadline")
                if deadline and item_id:
                    self.item_set(
                        ref,
                        item_id=item_id,
                        field=self.config.fields.deadline,
                        value=str(deadline),
                        value_kind="date",
                    )
                results.append(
                    {
                        "name": name,
                        "number": issue.get("number"),
                        "item_id": item_id,
                        "action": action,
                    }
                )
            except Exception as exc:
                name = pair.header_filepath
                try:
                    raw = yaml.safe_load(pair.header_path(root).read_text(encoding="utf-8")) or {}
                    if isinstance(raw, dict) and raw.get("name"):
                        name = str(raw["name"])
                except Exception:
                    pass
                failed.append({"name": name, "error": str(exc)})
        return {"project": ref.__dict__, "results": results, "failed": failed}

    def ingest_pairs(
        self,
        *,
        root: Path | None = None,
        manifest: Path | None = None,
        ref: ProjectRef | None = None,
    ) -> dict[str, Any]:
        root = root or project_task_root()
        manifest = manifest or project_pairs_file()
        ref = ref or self.default_ref()
        items = self.item_list(ref)
        pairs = load_pairs(manifest, task_root=root)
        updated: list[str] = []
        for pair in pairs:
            header_path = pair.header_path(root)
            raw = yaml.safe_load(header_path.read_text(encoding="utf-8")) or {}
            if not isinstance(raw, dict):
                continue
            match = self._match_pair_item(raw, items)
            if match is None:
                continue
            raw["item_id"] = _item_id(match)
            content = match.get("content") if isinstance(match.get("content"), dict) else {}
            issue_number = content.get("number")
            issue_payload: dict[str, Any] | None = None
            if issue_number:
                raw["issue_number"] = int(issue_number)
                issue_payload = self.gh.issue_view(int(issue_number))
            runtime = _read_item_runtime_fields(match, config=self.config, issue=issue_payload)
            raw.update(runtime)
            header_path.write_text(yaml.safe_dump(raw, sort_keys=True), encoding="utf-8")
            updated.append(str(raw.get("name") or pair.header_filepath))
        return {"project": ref.__dict__, "updated": updated}

    def sync_pairs(self, **kwargs: Any) -> dict[str, Any]:
        ingest = self.ingest_pairs(**kwargs)
        deploy = self.deploy_pairs(**kwargs)
        return {"ingest": ingest, "deploy": deploy}

    def recurrence_advance(
        self,
        *,
        root: Path | None = None,
        manifest: Path | None = None,
        ref: ProjectRef | None = None,
    ) -> dict[str, Any]:
        root = root or project_task_root()
        manifest = manifest or project_pairs_file()
        ref = ref or self.default_ref()
        today = date.today()
        advanced: list[dict[str, Any]] = []
        for pair in load_pairs(manifest, task_root=root):
            resolved = combine_task(pair, root)
            raw_meta = yaml.safe_load(pair.header_path(root).read_text(encoding="utf-8")) or {}
            meta = {**resolved.metadata.model_dump(), **(raw_meta if isinstance(raw_meta, dict) else {})}
            if not meta.get("enabled", True) or not self._is_maintenance(meta):
                continue
            issue_number = meta.get("issue_number")
            if not issue_number:
                continue
            issue = self.gh.issue_view(int(issue_number))
            if str(issue.get("state", "")).upper() not in {"CLOSED", "MERGED"}:
                continue
            interval = int(meta.get("interval") or 7)
            new_deadline = today + timedelta(days=interval)
            new_issue = self.gh.issue_create(
                title=str(meta["name"]),
                body=resolved.body,
                labels=list(meta.get("labels") or []) + [str(meta.get("tag") or "maintenance")],
            )
            added = self.item_add_url(str(new_issue["url"]), ref)
            item_id = str(added.get("id") or added.get("item", {}).get("id") or added.get("item_id") or "")
            if item_id:
                self.item_set(
                    ref,
                    item_id=item_id,
                    field=self.config.fields.deadline,
                    value=new_deadline.isoformat(),
                    value_kind="date",
                )
            header_path = pair.header_path(root)
            raw = yaml.safe_load(header_path.read_text(encoding="utf-8")) or {}
            raw["previous_issue_number"] = int(issue_number)
            raw["issue_number"] = int(new_issue["number"])
            raw["item_id"] = item_id
            raw["deadline"] = new_deadline.isoformat()
            raw["last_done"] = today.isoformat()
            header_path.write_text(yaml.safe_dump(raw, sort_keys=True), encoding="utf-8")
            advanced.append({"name": meta["name"], "old_number": issue_number, "new_number": new_issue["number"]})
        return {"project": ref.__dict__, "advanced": advanced}

    def _match_pair_item(self, meta: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any] | None:
        issue_number = meta.get("issue_number")
        item_id = meta.get("item_id")
        name = str(meta.get("name", ""))
        for item in items:
            if item_id and str(item.get("id")) == str(item_id):
                return item
            if issue_number and _content_number(item, "issue") == int(issue_number):
                return item
            content = item.get("content") if isinstance(item.get("content"), dict) else {}
            if name and str(content.get("title", "")) == name:
                return item
        return None

    def _validate_pair_metadata(self, meta: dict[str, Any]) -> None:
        if self._is_maintenance(meta) and not meta.get("deadline") and meta.get("interval") is None:
            raise ValueError("maintenance and tech-debt project pairs require deadline or interval")

    def _is_maintenance(self, meta: dict[str, Any]) -> bool:
        tag = str(meta.get("tag") or "").lower()
        labels = {str(label).lower() for label in meta.get("labels") or []}
        return tag in {"maintenance", "tech-debt"} or bool(labels & {"maintenance", "tech-debt"})


def default_project_seed_path() -> Path:
    return Path("config/project/examples/seed.yaml")


def recurrence_label_for_name(name: str) -> str:
    return f"recurrence:{slugify(name)}"
