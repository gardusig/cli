from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupRepository(BaseModel):
    path: str
    encrypted: bool = False


class BackupReplica(BaseModel):
    """Deploy target for tag zips (cloud provider or local USB path)."""

    type: str = "cloud"  # cloud | usb
    provider: str = ""  # google | onedrive | proton (cloud only)
    path: str = ""  # mount path (usb only)
    root: str = "git-tags"  # remote folder prefix (cloud only)
    name: str = ""  # optional display label


# Default local tag storage: iCloud Drive git-tags folder (macOS).
DEFAULT_TAGS_DIR = (
    "~/Library/Mobile Documents/com~apple~CloudDocs/git-tags"
)


class BackupConfig(BaseModel):
    tags_dir: str = DEFAULT_TAGS_DIR
    repositories: list[BackupRepository] = Field(default_factory=list)
    replicas: list[BackupReplica] = Field(default_factory=list)


class DriveProviderConfig(BaseModel):
    enabled: bool = False
    root: str = ""


class DrivesConfig(BaseModel):
    google: DriveProviderConfig = Field(default_factory=DriveProviderConfig)
    onedrive: DriveProviderConfig = Field(default_factory=DriveProviderConfig)
    proton: DriveProviderConfig = Field(default_factory=DriveProviderConfig)
    icloud: DriveProviderConfig = Field(default_factory=DriveProviderConfig)


class NotionPropertyMap(BaseModel):
    title: str = "Name"
    priority: str = "Priority"
    tag: str = "Tag"
    frequency: str = "Frequency"
    interval: str = "Interval"
    last_done: str = "Last done"
    forced_status: str = "Forced status"
    # Legacy keys (ignored by pair sync unless remapped in config).
    status: str = "Status"
    tags: str = "Tags"
    id: str = "ID"
    created: str = "Created"
    updated: str = "Updated"


class NotionConfig(BaseModel):
    database_id: str = ""
    task_root: str = ""
    task_directory: str = ""  # deprecated alias for task_root
    pairs_file: str = "tasks.pairs.json"
    cleanup_before_deploy: bool = True
    cleanup_before_upload: bool | None = None  # deprecated alias
    cleanup_before_import: bool | None = None  # deprecated alias
    properties: NotionPropertyMap = Field(default_factory=NotionPropertyMap)

    def model_post_init(self, __context: object) -> None:
        if self.cleanup_before_upload is not None:
            object.__setattr__(self, "cleanup_before_deploy", self.cleanup_before_upload)
        if self.cleanup_before_import is not None:
            object.__setattr__(self, "cleanup_before_deploy", self.cleanup_before_import)
        if not self.task_root.strip() and self.task_directory.strip():
            object.__setattr__(self, "task_root", self.task_directory)


def notion_cleanup_before_deploy(cfg: NotionConfig) -> bool:
    """Resolve deploy cleanup flag (supports deprecated config keys)."""
    if cfg.cleanup_before_import is not None:
        return cfg.cleanup_before_import
    if cfg.cleanup_before_upload is not None:
        return cfg.cleanup_before_upload
    return cfg.cleanup_before_deploy


class ChromeConfig(BaseModel):
    profile: str = "Default"
    bookmarks_file: str = ""
    downloads_dir: str = ""


class CliConfig(BaseModel):
    backup: BackupConfig = Field(default_factory=BackupConfig)
    drives: DrivesConfig = Field(default_factory=DrivesConfig)
    notion: NotionConfig = Field(default_factory=NotionConfig)
    chrome: ChromeConfig = Field(default_factory=ChromeConfig)


class CliSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLI_", extra="ignore")

    config_dir: Path = Path.home() / ".config" / "cli"


def project_root() -> Path:
    override = os.environ.get("CLI_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def load_local_env() -> None:
    """Load repo-root .env into os.environ (does not override existing vars)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = project_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


def default_config_dir() -> Path:
    env = os.environ.get("CLI_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    bundled = project_root() / "config"
    if bundled.exists():
        return bundled
    return Path.home() / ".config" / "cli"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _normalize_drives(raw: dict) -> dict:
    """Accept legacy boolean toggles or nested provider config."""
    drives: dict = {}
    for key, value in raw.items():
        if isinstance(value, bool):
            drives[key] = {"enabled": value, "root": ""}
        elif isinstance(value, dict):
            drives[key] = value
    return drives


def load_config(config_dir: Path | None = None) -> CliConfig:
    base = config_dir or default_config_dir()
    main_path = base / "config.yaml"
    drives_path = base / "drives.yaml"
    if not drives_path.exists() and base.name == "ci":
        drives_path = base.parent / "drives.yaml"

    merged: dict = {}
    merged.update(load_yaml(main_path))
    drives_data = load_yaml(drives_path)
    if "drives" in drives_data:
        merged["drives"] = _normalize_drives(drives_data["drives"])

    return CliConfig.model_validate(merged)


def tags_dir_path(config_dir: Path | None = None) -> Path:
    """Resolved absolute path to local tag zip storage (e.g. iCloud git-tags)."""
    cfg = load_config(config_dir)
    raw = Path(cfg.backup.tags_dir).expanduser()
    if raw.is_absolute():
        return raw
    return (project_root() / raw).resolve()


def tag_zip_basename(repo_basename: str, tag: str) -> str:
    """Zip filename stem: ``{repo}-{tag}`` (e.g. ``private-2026-06-23``)."""
    return f"{repo_basename}-{tag}"


def tag_from_zip_stem(repo_basename: str, stem: str) -> str:
    """Recover git tag from zip stem (prefixed or legacy bare tag)."""
    prefix = f"{repo_basename}-"
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return stem


def default_zip_path(repo_basename: str, tag: str, config_dir: Path | None = None) -> Path:
    return tags_dir_path(config_dir) / repo_basename / f"{tag_zip_basename(repo_basename, tag)}.zip"


def bookmarks_file_path(config_dir: Path | None = None) -> Path:
    """Resolved path for Chrome bookmarks HTML backup."""
    env = os.environ.get("CLI_BOOKMARKS_FILE")
    if env:
        return Path(env).expanduser().resolve()
    cfg = load_config(config_dir)
    raw = cfg.chrome.bookmarks_file.strip()
    if not raw:
        raise FileNotFoundError(
            "chrome.bookmarks_file is not configured. Set chrome.bookmarks_file in config/config.yaml."
        )
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def notion_task_root(config_dir: Path | None = None) -> Path:
    """Resolved path to local Notion task root (header/, body/, pairs manifest)."""
    env = os.environ.get("NOTION_TASK_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    cfg = load_config(config_dir)
    raw = cfg.notion.task_root.strip() or cfg.notion.task_directory.strip()
    if not raw:
        raise FileNotFoundError(
            "notion.task_root is not configured. Set notion.task_root in config/config.yaml "
            "to your private task directory."
        )
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def notion_pairs_file(config_dir: Path | None = None) -> Path:
    """Resolved path to tasks.pairs.json manifest.

    When ``pairs_file`` is a bare filename (e.g. ``tasks.pairs.json``), it lives under
    ``notion.task_root``. When it includes a directory (e.g. ``config/notion/tasks.pairs.json``)
    or is absolute, header/body stay under ``task_root`` and only the manifest path differs.
    """
    cfg = load_config(config_dir)
    raw = cfg.notion.pairs_file.strip() or "tasks.pairs.json"
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    if len(path.parts) > 1:
        return (project_root() / path).resolve()
    return notion_task_root(config_dir) / path.name


def notion_tasks_dir(config_dir: Path | None = None) -> Path:
    """Deprecated alias for notion_task_root()."""
    return notion_task_root(config_dir)


def notion_body_template_file(config_dir: Path | None = None) -> Path:
    """Default body scaffold for new task pairs (ingest creates empty bodies)."""
    return (project_root() / "config" / "notion" / "templates" / "body.md").resolve()


def notion_database_id(
    notion: NotionConfig | None = None,
    *,
    config_dir: Path | None = None,
) -> str:
    """Notion database id from NOTION_DATABASE_ID env or config."""
    env = os.environ.get("NOTION_DATABASE_ID", "").strip()
    if env:
        return env
    n = notion or load_config(config_dir).notion
    db = n.database_id.strip()
    if not db:
        raise RuntimeError(
            "notion.database_id is not configured. Set NOTION_DATABASE_ID or notion.database_id in config."
        )
    return db


def require_notion_token(cfg: CliConfig | None = None) -> str:
    """Notion integration token from NOTION_TOKEN (never commit to config)."""
    token = os.environ.get("NOTION_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "NOTION_TOKEN is not set. Export a Notion integration token to your environment."
        )
    notion_database_id((cfg or load_config()).notion)
    return token


def backup_zip_password() -> str | None:
    """Zip encryption password from BACKUP_ZIP_PASSWORD (never commit to config)."""
    value = os.environ.get("BACKUP_ZIP_PASSWORD", "").strip()
    return value or None


def require_backup_zip_password() -> str:
    password = backup_zip_password()
    if not password:
        raise RuntimeError(
            "BACKUP_ZIP_PASSWORD is not set. Export a zip password for encrypted "
            "backup repositories (see .env.example)."
        )
    return password


def backup_repository_entry(
    repo_path: Path,
    config_dir: Path | None = None,
) -> BackupRepository | None:
    """Config row for a repository path, if listed in backup.repositories."""
    resolved = repo_path.expanduser().resolve()
    for entry in load_config(config_dir).backup.repositories:
        if Path(entry.path).expanduser().resolve() == resolved:
            return entry
    return None


def repo_encrypt_backup(repo_path: Path, config_dir: Path | None = None) -> bool:
    entry = backup_repository_entry(repo_path, config_dir)
    return bool(entry and entry.encrypted)


def chrome_downloads_dir(config_dir: Path | None = None) -> Path:
    """Downloads folder polled during Chrome bookmark export."""
    env = os.environ.get("CLI_DOWNLOADS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    raw = load_config(config_dir).chrome.downloads_dir.strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / "Downloads"
