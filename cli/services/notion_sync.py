"""Notion task board sync — ingest / deploy / cleanup."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cli.models.task import TaskMetadata, TaskPair
from cli.providers.notion import NotionClient
from cli.services.notion_markdown import normalize_task_body
from cli.services.notion_pairs import (
    build_from_disk,
    combine_task,
    dump_header,
    load_header,
    load_pairs,
    pair_file_warning,
    save_pairs,
    scan_task_root,
    slugify,
    task_name,
)
from cli.utils.config import (
    NotionConfig,
    load_config,
    notion_body_template_file,
    notion_pairs_file,
    notion_task_root,
)


@dataclass
class NotionSyncResult:
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)


def _pair_index(pairs: list[TaskPair], task_root: Path) -> dict[str, TaskPair]:
    out: dict[str, TaskPair] = {}
    for pair in pairs:
        if pair_file_warning(pair, task_root):
            continue
        out[task_name(pair, task_root)] = pair
    return out


def export_tasks(
    task_root: Path | None = None,
    *,
    token: str,
    config: NotionConfig,
) -> NotionSyncResult:
    """Notion → local: update header/body pairs from board pages."""
    root = task_root or notion_task_root()
    manifest = notion_pairs_file()
    pairs = load_pairs(manifest, task_root=root) if manifest.is_file() else []
    pair_by_name = _pair_index(pairs, root)

    result = NotionSyncResult()
    result.warnings.extend(scan_task_root(root).warnings)

    with NotionClient(token, config=config) as client:
        pages = client.query_database_pages(config.database_id)
        titles: list[str] = []
        for page in pages:
            if page.get("archived"):
                continue
            title = client.page_title(page)
            if not title:
                result.failed += 1
                continue
            if title in titles:
                raise ValueError(f"Duplicate Notion task title: {title!r}")
            titles.append(title)

            meta_fields = client.page_metadata(page)
            body = client.page_body_markdown(page["id"], task_name=title)
            body = normalize_task_body(body)

            if title in pair_by_name:
                pair = pair_by_name[title]
                existing = load_header(pair.header_path(root))
                updated = TaskMetadata(
                    name=title,
                    priority=meta_fields.get("priority") or existing.priority,
                    tag=meta_fields.get("tag") or existing.tag,
                    frequency=meta_fields.get("frequency") or existing.frequency,
                    interval=meta_fields.get("interval")
                    if meta_fields.get("interval") is not None
                    else existing.interval,
                    last_done=meta_fields.get("last_done") or existing.last_done,
                    forced_status=meta_fields.get("forced_status") or existing.forced_status,
                    enabled=existing.enabled,
                )
                dump_header(pair.header_path(root), updated)
                pair.body_path(root).write_text(body, encoding="utf-8")
                result.processed += 1
            else:
                slug = slugify(title)
                meta_rel = f"header/misc/{slug}.yaml"
                body_rel = f"body/misc/{slug}.md"
                meta_path = root / meta_rel
                body_path = root / body_rel
                if meta_path.exists():
                    stem = slug
                    n = 2
                    while meta_path.exists():
                        stem = f"{slug}-{n}"
                        meta_rel = f"header/misc/{stem}.yaml"
                        body_rel = f"body/misc/{stem}.md"
                        meta_path = root / meta_rel
                        body_path = root / body_rel
                        n += 1

                new_meta = TaskMetadata(
                    name=title,
                    priority=meta_fields.get("priority"),
                    tag=meta_fields.get("tag"),
                    frequency=meta_fields.get("frequency"),
                    interval=meta_fields.get("interval"),
                    last_done=meta_fields.get("last_done"),
                    forced_status=meta_fields.get("forced_status"),
                    enabled=True,
                )
                dump_header(meta_path, new_meta)
                body_path.parent.mkdir(parents=True, exist_ok=True)
                if not body.strip():
                    template = notion_body_template_file()
                    body = (
                        template.read_text(encoding="utf-8")
                        if template.is_file()
                        else "## Steps\n\n1. …\n\n## Done when\n\n- [ ] …\n"
                    )
                body_path.write_text(normalize_task_body(body), encoding="utf-8")

                new_pair = TaskPair(
                    header_filepath=meta_rel,
                    body_filepath=body_rel,
                )
                pairs.append(new_pair)
                pair_by_name[title] = new_pair
                result.processed += 1

        save_pairs(manifest, pairs)
    return result


def import_tasks(
    task_root: Path | None = None,
    *,
    token: str,
    config: NotionConfig,
    cleanup_first: bool | None = None,
) -> NotionSyncResult:
    """Local → Notion: archive board (optional) then create pages from pairs."""
    root = task_root or notion_task_root()
    manifest = notion_pairs_file()
    pairs = load_pairs(manifest, task_root=root)
    result = NotionSyncResult()
    result.warnings.extend(scan_task_root(root).warnings)

    do_cleanup = config.cleanup_before_deploy if cleanup_first is None else cleanup_first

    with NotionClient(token, config=config) as client:
        if do_cleanup:
            client.archive_all_in_database(config.database_id)

        for pair in pairs:
            warning = pair_file_warning(pair, root)
            if warning:
                result.warnings.append(warning)
                result.skipped += 1
                continue
            task = combine_task(pair, root)
            if not task.metadata.enabled:
                result.warnings.append(f"disabled (skipped): {task.metadata.name}")
                result.skipped += 1
                continue
            payload = task.metadata.model_dump(
                exclude={"name", "enabled"},
                exclude_none=True,
            )
            try:
                client.create_database_page(
                    config.database_id,
                    title=task.metadata.name,
                    metadata=payload,
                    body_markdown=task.body,
                )
                result.processed += 1
            except Exception:
                result.failed += 1
                raise

    return result


def cleanup_board(
    *,
    token: str,
    config: NotionConfig,
) -> NotionSyncResult:
    """Archive every page in the configured Notion database."""
    with NotionClient(token, config=config) as client:
        count = client.archive_all_in_database(config.database_id)
    return NotionSyncResult(processed=count)


def build_pairs_manifest(
    task_root: Path | None = None,
    *,
    config_dir: Path | None = None,
) -> NotionSyncResult:
    """Scan header/ + body/ and write tasks.pairs.json (under task root or pairs_file path)."""
    root = task_root or notion_task_root(config_dir)
    pairs = build_from_disk(root)
    save_pairs(notion_pairs_file(config_dir), pairs)
    return NotionSyncResult(processed=len(pairs))
