"""Load, validate, and build tasks.pairs.json manifest."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from shuttle.models.task import PairScanResult, ResolvedTaskPair, TaskMetadata, TaskPair
from shuttle.services.notion_markdown import normalize_task_body

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Filesystem-safe stem from a task name."""
    base = _SLUG_RE.sub("-", title.lower().strip())
    return base.strip("-") or "task"


def load_pairs(manifest_path: Path, *, task_root: Path | None = None) -> list[TaskPair]:
    """Load manifest and validate unique task names from metadata yaml."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Pairs manifest not found: {manifest_path}")
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected JSON array in {manifest_path}")
    pairs = [_normalize_pair_entry(item) for item in raw]
    if task_root is not None:
        _validate_unique_names(task_root, pairs)
    return pairs


def _normalize_pair_entry(item: object) -> TaskPair:
    if not isinstance(item, dict):
        raise ValueError("Each manifest entry must be an object")
    data = dict(item)
    # Legacy keys id/name in manifest are ignored.
    data.pop("id", None)
    data.pop("name", None)
    return TaskPair.model_validate(data)


def _validate_unique_names(task_root: Path, pairs: list[TaskPair]) -> None:
    seen: set[str] = set()
    for pair in pairs:
        if pair_file_warning(pair, task_root):
            continue
        name = task_name(pair, task_root)
        if name in seen:
            raise ValueError(f"Duplicate task name: {name!r}")
        seen.add(name)


def task_name(pair: TaskPair, task_root: Path) -> str:
    """Resolve unique task name from metadata yaml."""
    meta = load_metadata(pair.metadata_path(task_root))
    return meta.name


def save_pairs(manifest_path: Path, pairs: list[TaskPair]) -> None:
    """Write path-only pairs manifest (sorted by metadata path)."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(pairs, key=lambda p: p.metadata_filepath.casefold())
    payload = [
        {
            "metadata_filepath": p.metadata_filepath,
            "body_filepath": p.body_filepath,
        }
        for p in ordered
    ]
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_metadata(path: Path) -> TaskMetadata:
    if not path.is_file():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return TaskMetadata.model_validate(data)


def dump_metadata(path: Path, metadata: TaskMetadata) -> None:
    """Write metadata yaml including required name."""
    data = metadata.model_dump(exclude_none=True)
    if metadata.enabled is True:
        data.pop("enabled", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=True, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def validate_pair_files(task_root: Path, pair: TaskPair) -> None:
    warning = pair_file_warning(pair, task_root)
    if warning:
        raise FileNotFoundError(warning)


def _metadata_relative(path: Path, task_root: Path) -> str:
    return path.relative_to(task_root).as_posix()


def _body_path_for_metadata(meta_rel: str) -> str:
    """metadata/foo/bar.yaml → body/foo/bar.md"""
    p = Path(meta_rel)
    if p.suffix not in {".yaml", ".yml"}:
        raise ValueError(f"Not a yaml metadata path: {meta_rel}")
    if not p.parts or p.parts[0] != "metadata":
        raise ValueError(f"Metadata path must start with metadata/: {meta_rel}")
    return str(Path("body", *p.parts[1:]).with_suffix(".md"))


def pair_file_warning(pair: TaskPair, task_root: Path) -> str | None:
    """Return a warning when metadata/body half of a pair is missing."""
    meta = pair.metadata_path(task_root)
    body = pair.body_path(task_root)
    if not meta.is_file() and not body.is_file():
        return f"pair missing metadata and body: {pair.metadata_filepath}"
    if not meta.is_file():
        return f"body without metadata: {pair.body_filepath}"
    if not body.is_file():
        return f"metadata without body: {pair.metadata_filepath}"
    try:
        if not load_metadata(meta).name.strip():
            return f"metadata missing name: {pair.metadata_filepath}"
    except Exception as exc:
        return f"invalid metadata {pair.metadata_filepath}: {exc}"
    return None


def combine_task(pair: TaskPair, task_root: Path) -> ResolvedTaskPair:
    """Load metadata + body into one deployable/inspectable task."""
    warning = pair_file_warning(pair, task_root)
    if warning:
        raise FileNotFoundError(warning)
    meta = load_metadata(pair.metadata_path(task_root))
    body = normalize_task_body(pair.body_path(task_root).read_text(encoding="utf-8"))
    return ResolvedTaskPair(pair=pair, metadata=meta, body=body)


def scan_task_root(task_root: Path) -> PairScanResult:
    """Discover complete pairs; warn on orphan metadata or body files."""
    warnings: list[str] = []
    pairs: list[TaskPair] = []
    meta_dir = task_root / "metadata"
    body_dir = task_root / "body"
    if not meta_dir.is_dir() and not body_dir.is_dir():
        return PairScanResult(warnings=["task root has no metadata/ or body/"])

    matched_bodies: set[Path] = set()
    if meta_dir.is_dir():
        for meta_path in sorted(meta_dir.rglob("*.yaml")):
            rel = _metadata_relative(meta_path, task_root)
            body_rel = _body_path_for_metadata(rel)
            body_path = task_root / body_rel
            if not body_path.is_file():
                warnings.append(f"metadata without body: {rel}")
                continue
            try:
                meta = load_metadata(meta_path)
                if not meta.name.strip():
                    warnings.append(f"metadata missing name: {rel}")
                    continue
            except Exception as exc:
                warnings.append(f"invalid metadata {rel}: {exc}")
                continue
            pairs.append(
                TaskPair(metadata_filepath=rel, body_filepath=body_rel)
            )
            matched_bodies.add(body_path)

    if body_dir.is_dir():
        for body_path in sorted(body_dir.rglob("*.md")):
            if body_path in matched_bodies:
                continue
            rel = _metadata_relative(body_path, task_root)
            warnings.append(f"body without metadata: {rel}")

    try:
        _validate_unique_names(task_root, pairs)
    except ValueError as exc:
        warnings.append(str(exc))
        pairs = []

    return PairScanResult(pairs=pairs, warnings=warnings)


def build_from_disk(task_root: Path) -> list[TaskPair]:
    """Scan metadata/**/*.yaml and build pairs (raises if orphans or duplicates)."""
    scan = scan_task_root(task_root)
    if scan.warnings:
        raise ValueError("; ".join(scan.warnings))
    return scan.pairs
