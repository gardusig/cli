"""Deterministic GitHub repository inventory via gh api."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from src.utils.config import project_root


def _gh_json(path: str) -> Any:
    result = subprocess.run(["gh", "api", path], check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


def _repo_registry_path() -> Path:
    return project_root() / "config" / "gh" / "repos.yaml"


def load_repo_registry(path: Path | None = None) -> list[dict[str, Any]]:
    data = yaml.safe_load((path or _repo_registry_path()).read_text(encoding="utf-8")) or {}
    repos = data.get("repositories") or []
    if not isinstance(repos, list):
        raise ValueError("config/gh/repos.yaml must contain a repositories list")
    return [dict(repo) for repo in repos]


def _extension(path: str) -> str:
    name = Path(path).name
    if "." not in name:
        return "(none)"
    return Path(path).suffix.lower() or "(none)"


def _tree_lines(slug: str, paths: list[str], *, depth: int) -> list[str]:
    dirs: set[tuple[str, ...]] = set()
    files: set[tuple[str, ...]] = set()
    for raw in paths:
        parts = tuple(part for part in raw.split("/") if part)
        if not parts:
            continue
        clipped = parts[:depth]
        if len(parts) <= depth:
            files.add(clipped)
        for idx in range(1, min(len(parts), depth) + 1):
            dirs.add(parts[:idx])

    lines = [f"{slug}/"]
    for entry in sorted(dirs | files):
        indent = "  " * (len(entry) - 1)
        suffix = "/" if entry in dirs and entry not in files else ""
        lines.append(f"{indent}{entry[-1]}{suffix}")
    return lines


def inventory_repo(repository: str, *, ref: str = "main", depth: int = 3) -> dict[str, Any]:
    meta = _gh_json(f"repos/{repository}")
    tree = _gh_json(f"repos/{repository}/git/trees/{ref}?recursive=1")
    entries = tree.get("tree") or []
    blobs = [entry for entry in entries if entry.get("type") == "blob"]
    paths = [str(entry["path"]) for entry in blobs]
    extensions = Counter(_extension(path) for path in paths)
    slug = repository.rsplit("/", 1)[-1]
    return {
        "repository": repository,
        "slug": slug,
        "ref": ref,
        "default_branch": meta.get("default_branch", ""),
        "size_kb": meta.get("size", 0),
        "file_count": len(paths),
        "extensions": dict(sorted(extensions.items())),
        "tree": _tree_lines(slug, paths, depth=depth),
        "snapshot": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def render_inventory_markdown(inv: dict[str, Any]) -> str:
    ext_rows = "\n".join(
        f"| `{ext}` | {count} |" for ext, count in sorted(inv["extensions"].items())
    )
    tree = "\n".join(inv["tree"])
    return f"""# {inv['repository']}

- Branch: `{inv['ref']}`
- Default branch: `{inv['default_branch']}`
- Size: {inv['size_kb']} KB
- Files: {inv['file_count']}
- Snapshot: {inv['snapshot']}

## Extensions

| Extension | Files |
|-----------|------:|
{ext_rows}

## Tree (Depth <= 3)

```text
{tree}
```
"""


def sync_wiki_repositories(
    wiki_dir: Path,
    *,
    owner: str = "gardusig",
    ref: str = "main",
    depth: int = 3,
    include_private: bool = True,
) -> list[Path]:
    repos_dir = wiki_dir / "repositories"
    repos_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for row in load_repo_registry():
        if row.get("wiki_inventory") is False:
            continue
        if not include_private and row.get("visibility") == "private":
            continue
        repository = str(row.get("repository") or f"{owner}/{row['slug']}")
        inv = inventory_repo(repository, ref=ref, depth=depth)
        path = repos_dir / f"{inv['slug']}.md"
        path.write_text(render_inventory_markdown(inv), encoding="utf-8")
        written.append(path)

    index = "# Repositories\n\n" + "\n".join(
        f"- [{path.stem}](repositories/{path.name})" for path in sorted(written)
    )
    (wiki_dir / "README.md").write_text(index + "\n", encoding="utf-8")
    return written
