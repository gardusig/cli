"""Load, validate, and build tasks.pairs.json manifest."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from cli.models.task import PairScanResult, ResolvedTaskPair, TaskMetadata, TaskPair
from cli.services.notion_markdown import normalize_task_body

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Filesystem-safe stem from a task name."""
    base = _SLUG_RE.sub("-", title.lower().strip())
    return base.strip("-") or "task"


def load_pairs(manifest_path: Path, *, task_root: Path | None = None) -> list[TaskPair]:
    """Load manifest and validate unique task names from header yaml."""
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
    """Resolve unique task name from header yaml."""
    meta = load_header(pair.header_path(task_root))
    return meta.name


def save_pairs(manifest_path: Path, pairs: list[TaskPair]) -> None:
    """Write path-only pairs manifest (sorted by header path)."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(pairs, key=lambda p: p.header_filepath.casefold())
    payload = [
        {
            "header_filepath": p.header_filepath,
            "body_filepath": p.body_filepath,
        }
        for p in ordered
    ]
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_header(path: Path) -> TaskMetadata:
    if not path.is_file():
        raise FileNotFoundError(f"Header file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return TaskMetadata.model_validate(data)


def dump_header(path: Path, metadata: TaskMetadata) -> None:
    """Write header yaml including required name."""
    data = metadata.model_dump(exclude_none=True)
    if metadata.enabled is True:
        data.pop("enabled", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=True, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


# Back-compat aliases for internal callers during transition (same module).
load_metadata = load_header
dump_metadata = dump_header


def validate_pair_files(task_root: Path, pair: TaskPair) -> None:
    warning = pair_file_warning(pair, task_root)
    if warning:
        raise FileNotFoundError(warning)


def _header_relative(path: Path, task_root: Path) -> str:
    return path.relative_to(task_root).as_posix()


def _body_path_for_header(header_rel: str) -> str:
    """header/foo/bar.yaml → body/foo/bar.md"""
    p = Path(header_rel)
    if p.suffix not in {".yaml", ".yml"}:
        raise ValueError(f"Not a yaml header path: {header_rel}")
    if not p.parts or p.parts[0] != "header":
        raise ValueError(f"Header path must start with header/: {header_rel}")
    return str(Path("body", *p.parts[1:]).with_suffix(".md"))


def pair_file_warning(pair: TaskPair, task_root: Path) -> str | None:
    """Return a warning when header/body half of a pair is missing."""
    header = pair.header_path(task_root)
    body = pair.body_path(task_root)
    if not header.is_file() and not body.is_file():
        return f"pair missing header and body: {pair.header_filepath}"
    if not header.is_file():
        return f"body without header: {pair.body_filepath}"
    if not body.is_file():
        return f"header without body: {pair.header_filepath}"
    try:
        if not load_header(header).name.strip():
            return f"header missing name: {pair.header_filepath}"
    except Exception as exc:
        return f"invalid header {pair.header_filepath}: {exc}"
    return None


def combine_task(pair: TaskPair, task_root: Path) -> ResolvedTaskPair:
    """Load header + body into one deployable/inspectable task."""
    warning = pair_file_warning(pair, task_root)
    if warning:
        raise FileNotFoundError(warning)
    meta = load_header(pair.header_path(task_root))
    body = normalize_task_body(pair.body_path(task_root).read_text(encoding="utf-8"))
    return ResolvedTaskPair(pair=pair, metadata=meta, body=body)


def scan_task_root(task_root: Path) -> PairScanResult:
    """Discover complete pairs; warn on orphan header or body files."""
    warnings: list[str] = []
    pairs: list[TaskPair] = []
    header_dir = task_root / "header"
    body_dir = task_root / "body"
    if not header_dir.is_dir() and not body_dir.is_dir():
        return PairScanResult(warnings=["task root has no header/ or body/"])

    matched_bodies: set[Path] = set()
    if header_dir.is_dir():
        for header_path in sorted(header_dir.rglob("*.yaml")):
            rel = _header_relative(header_path, task_root)
            body_rel = _body_path_for_header(rel)
            body_path = task_root / body_rel
            if not body_path.is_file():
                warnings.append(f"header without body: {rel}")
                continue
            try:
                meta = load_header(header_path)
                if not meta.name.strip():
                    warnings.append(f"header missing name: {rel}")
                    continue
            except Exception as exc:
                warnings.append(f"invalid header {rel}: {exc}")
                continue
            pairs.append(
                TaskPair(header_filepath=rel, body_filepath=body_rel)
            )
            matched_bodies.add(body_path)

    if body_dir.is_dir():
        for body_path in sorted(body_dir.rglob("*.md")):
            if body_path in matched_bodies:
                continue
            rel = _header_relative(body_path, task_root)
            warnings.append(f"body without header: {rel}")

    try:
        _validate_unique_names(task_root, pairs)
    except ValueError as exc:
        warnings.append(str(exc))
        pairs = []

    return PairScanResult(pairs=pairs, warnings=warnings)


@dataclass
class PairDeployRollout:
    """Deploy readiness from header yaml (enabled flag)."""

    enabled: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    broken: list[str] = field(default_factory=list)


def pair_deploy_rollout(task_root: Path, pairs: list[TaskPair]) -> PairDeployRollout:
    """Classify manifest pairs for deploy: enabled, disabled (paused), or broken."""
    rollout = PairDeployRollout()
    for pair in pairs:
        warning = pair_file_warning(pair, task_root)
        if warning:
            rollout.broken.append(f"{pair.header_filepath} ({warning})")
            continue
        meta = load_header(pair.header_path(task_root))
        if meta.enabled:
            rollout.enabled.append(meta.name)
        else:
            rollout.disabled.append(meta.name)
    return rollout


def build_from_disk(task_root: Path) -> list[TaskPair]:
    """Scan header/**/*.yaml and build pairs (raises if orphans or duplicates)."""
    scan = scan_task_root(task_root)
    if scan.warnings:
        raise ValueError("; ".join(scan.warnings))
    return scan.pairs
