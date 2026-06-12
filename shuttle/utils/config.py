from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupRepository(BaseModel):
    path: str


# Default local tag storage: iCloud Drive git-tags folder (macOS).
DEFAULT_TAGS_DIR = (
    "~/Library/Mobile Documents/com~apple~CloudDocs/git-tags"
)


class BackupConfig(BaseModel):
    tags_dir: str = DEFAULT_TAGS_DIR
    repositories: list[BackupRepository] = Field(default_factory=list)


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
    status: str = "Status"
    priority: str = "Priority"
    tags: str = "Tags"
    id: str = "ID"
    created: str = "Created"
    updated: str = "Updated"


class NotionConfig(BaseModel):
    database_id: str = ""
    task_directory: str = "data/tasks"
    cleanup_before_deploy: bool = False
    cleanup_before_upload: bool | None = None  # deprecated alias
    cleanup_before_import: bool | None = None  # deprecated alias
    properties: NotionPropertyMap = Field(default_factory=NotionPropertyMap)

    def model_post_init(self, __context: object) -> None:
        if self.cleanup_before_upload is not None:
            object.__setattr__(self, "cleanup_before_deploy", self.cleanup_before_upload)
        if self.cleanup_before_import is not None:
            object.__setattr__(self, "cleanup_before_deploy", self.cleanup_before_import)


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


class ShuttleConfig(BaseModel):
    backup: BackupConfig = Field(default_factory=BackupConfig)
    drives: DrivesConfig = Field(default_factory=DrivesConfig)
    notion: NotionConfig = Field(default_factory=NotionConfig)
    chrome: ChromeConfig = Field(default_factory=ChromeConfig)


class ShuttleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHUTTLE_", extra="ignore")

    config_dir: Path = Path.home() / ".config" / "shuttle-cli"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_config_dir() -> Path:
    env = os.environ.get("SHUTTLE_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    bundled = project_root() / "config"
    if bundled.exists():
        return bundled
    return Path.home() / ".config" / "shuttle-cli"


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


def load_config(config_dir: Path | None = None) -> ShuttleConfig:
    base = config_dir or default_config_dir()
    main_path = base / "config.yaml"
    drives_path = base / "drives.yaml"

    merged: dict = {}
    merged.update(load_yaml(main_path))
    drives_data = load_yaml(drives_path)
    if "drives" in drives_data:
        merged["drives"] = _normalize_drives(drives_data["drives"])

    return ShuttleConfig.model_validate(merged)


def tags_dir_path(config_dir: Path | None = None) -> Path:
    """Resolved absolute path to local tag zip storage (e.g. iCloud git-tags)."""
    cfg = load_config(config_dir)
    raw = Path(cfg.backup.tags_dir).expanduser()
    if raw.is_absolute():
        return raw
    return (project_root() / raw).resolve()


def default_zip_path(repo_basename: str, tag: str, config_dir: Path | None = None) -> Path:
    return tags_dir_path(config_dir) / repo_basename / f"{tag}.zip"


def bookmarks_file_path(config_dir: Path | None = None) -> Path:
    """Resolved path for Chrome bookmarks HTML backup."""
    env = os.environ.get("SHUTTLE_BOOKMARKS_FILE")
    if env:
        return Path(env).expanduser().resolve()
    cfg = load_config(config_dir)
    raw = cfg.chrome.bookmarks_file.strip()
    if raw:
        path = Path(raw).expanduser()
        if path.is_absolute():
            return path.resolve()
        return (project_root() / path).resolve()
    return (project_root() / "data" / "bookmarks" / "bookmarks.html").resolve()


def notion_tasks_dir(config_dir: Path | None = None) -> Path:
    """Resolved path to local Notion task markdown folder."""
    cfg = load_config(config_dir)
    raw = Path(cfg.notion.task_directory.strip() or "data/tasks")
    if raw.is_absolute():
        return raw.resolve()
    return (project_root() / raw).resolve()


def require_notion_token(cfg: ShuttleConfig | None = None) -> str:
    """Notion integration token from NOTION_TOKEN (never commit to config)."""
    token = os.environ.get("NOTION_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "NOTION_TOKEN is not set. Export a Notion integration token to your environment."
        )
    notion = (cfg or load_config()).notion
    if not notion.database_id.strip():
        raise RuntimeError(
            "notion.database_id is not configured. Set it in config/config.yaml."
        )
    return token


def chrome_downloads_dir(config_dir: Path | None = None) -> Path:
    """Downloads folder polled during Chrome bookmark export."""
    env = os.environ.get("SHUTTLE_DOWNLOADS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    raw = load_config(config_dir).chrome.downloads_dir.strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / "Downloads"
