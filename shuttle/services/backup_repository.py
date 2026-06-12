"""Local git-tags backup (iCloud or configured path): sync, list, delete, status."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from shuttle.services.git_shortcuts import GitShortcuts
from shuttle.utils.config import load_config, tags_dir_path

@dataclass
class RepoBackupStatus:
    name: str
    path: Path
    git_tags: list[str] = field(default_factory=list)
    downloaded: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class SyncResult:
    created: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def resolve_repo_path(path: str | None) -> Path:
    raw = Path(path or ".").expanduser().resolve()
    if not raw.is_dir():
        raise RuntimeError(f"Not a directory: {raw}")
    git_dir = raw / ".git"
    if not git_dir.exists():
        raise RuntimeError(f"Not a git repository: {raw}")
    return raw


def repo_folder_name(repo_path: Path) -> str:
    return repo_path.name


def repo_storage_dir(repo_path: Path, config_dir: Path | None = None) -> Path:
    return tags_dir_path(config_dir) / repo_folder_name(repo_path)


def list_downloaded_tags(repo_path: Path, config_dir: Path | None = None) -> list[str]:
    storage = repo_storage_dir(repo_path, config_dir)
    if not storage.is_dir():
        return []
    return sorted(p.stem for p in storage.glob("*.zip") if p.is_file())


def list_git_tags(repo_path: Path) -> list[str]:
    return GitShortcuts(top=str(repo_path)).list_local_tags()


def backup_status(config_dir: Path | None = None) -> list[RepoBackupStatus]:
    cfg = load_config(config_dir)
    rows: list[RepoBackupStatus] = []
    for entry in cfg.backup.repositories:
        repo_path = Path(entry.path).expanduser().resolve()
        if not repo_path.is_dir():
            continue
        git_tags = list_git_tags(repo_path) if (repo_path / ".git").exists() else []
        downloaded = list_downloaded_tags(repo_path, config_dir)
        missing = sorted(set(git_tags) - set(downloaded))
        rows.append(
            RepoBackupStatus(
                name=repo_folder_name(repo_path),
                path=repo_path,
                git_tags=git_tags,
                downloaded=downloaded,
                missing=missing,
            )
        )
    return sorted(rows, key=lambda r: r.name)


def ingest_repositories(
    path: str | None = None,
    config_dir: Path | None = None,
) -> list[tuple[Path, SyncResult]]:
    """Zip all git tags for one repo or every path in backup.repositories."""
    if path is not None:
        repo = resolve_repo_path(path)
        return [(repo, sync_repo(str(repo), config_dir))]
    cfg = load_config(config_dir)
    if not cfg.backup.repositories:
        raise RuntimeError(
            "No repositories configured. Add backup.repositories to config.yaml "
            "or pass a repository path to ingest."
        )
    rows: list[tuple[Path, SyncResult]] = []
    for entry in cfg.backup.repositories:
        repo_path = Path(entry.path).expanduser().resolve()
        try:
            rows.append((repo_path, sync_repo(str(repo_path), config_dir)))
        except RuntimeError as exc:
            failed = SyncResult()
            failed.failed.append(("", str(exc)))
            rows.append((repo_path, failed))
    return rows


def sync_repo(path: str | None = None, config_dir: Path | None = None) -> SyncResult:
    repo_path = resolve_repo_path(path)
    svc = GitShortcuts(top=str(repo_path))
    storage = repo_storage_dir(repo_path, config_dir)
    storage.mkdir(parents=True, exist_ok=True)
    result = SyncResult()
    for tag in svc.list_local_tags():
        dest = storage / f"{tag}.zip"
        existed = dest.is_file()
        try:
            svc.zip_tag(tag, dest)
            if existed:
                result.replaced.append(tag)
            else:
                result.created.append(tag)
        except Exception as exc:  # noqa: BLE001 — collect per-tag failures
            result.failed.append((tag, str(exc)))
    return result


def delete_repo_tag(path: str, tag: str, config_dir: Path | None = None) -> Path:
    repo_path = resolve_repo_path(path)
    dest = repo_storage_dir(repo_path, config_dir) / f"{tag}.zip"
    if not dest.is_file():
        raise RuntimeError(f"No backup zip for tag {tag}: {dest}")
    dest.unlink()
    return dest


def format_status_lines(rows: list[RepoBackupStatus]) -> list[str]:
    lines: list[str] = []
    if not rows:
        lines.append(
            "No repositories configured. Add backup.repositories to config.yaml "
            "for drive status / ingest."
        )
        return lines
    for row in rows:
        lines.append(f"Repository: {row.name}  ({row.path})")
        lines.append(f"  Local tags (git):     {'  '.join(row.git_tags) or '(none)'}")
        lines.append(f"  Downloaded (zips):    {'  '.join(row.downloaded) or '(none)'}")
        lines.append(f"  Missing locally:      {'  '.join(row.missing) or '(none)'}")
        lines.append("")
    return lines
