from __future__ import annotations

import os
from pathlib import Path

import yaml
from platformdirs import user_config_dir
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


# Empty until `cli configure set backup.tags_dir` (no baked-in home paths).
DEFAULT_TAGS_DIR = ""


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
    link: str = "link"
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
    link_branch: str = "main"
    link_repo: str = ""  # owner/repo for runbook URLs in Notion (git-hosted tasks/)
    labels_manifest: str = "labels.manifest.yaml"
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


class ChromeProfileConfig(BaseModel):
    bookmarks_file: str = ""


class GhIssuesPruneConfig(BaseModel):
    closed_older_than: str = "7d"


class GhIssuesConfig(BaseModel):
    repo: str = ""
    labels_manifest: str = ""
    prune: GhIssuesPruneConfig = Field(default_factory=GhIssuesPruneConfig)


class GhConfig(BaseModel):
    issues: GhIssuesConfig = Field(default_factory=GhIssuesConfig)


class ChromeConfig(BaseModel):
    profile: str = "Default"
    bookmarks_file: str = ""
    downloads_dir: str = ""
    photos_dir: str = ""
    photos_takeout_dir: str = ""
    profiles: dict[str, ChromeProfileConfig] = Field(default_factory=dict)
    snapshots_dir: str = ""
    snapshot_retention: int = 0


class AuthCredentialConfig(BaseModel):
    env: str = ""
    token_file: str = ""


class AuthConfig(BaseModel):
    notion: AuthCredentialConfig = Field(default_factory=AuthCredentialConfig)
    gh: AuthCredentialConfig = Field(default_factory=AuthCredentialConfig)
    backup: AuthCredentialConfig = Field(default_factory=AuthCredentialConfig)
    deepseek: AuthCredentialConfig = Field(default_factory=AuthCredentialConfig)
    pypi: AuthCredentialConfig = Field(default_factory=AuthCredentialConfig)
    google_drive: AuthCredentialConfig = Field(
        default_factory=lambda: AuthCredentialConfig(env="GOOGLE_DRIVE_TOKEN")
    )
    onedrive: AuthCredentialConfig = Field(
        default_factory=lambda: AuthCredentialConfig(env="ONEDRIVE_TOKEN")
    )


class CliConfig(BaseModel):
    backup: BackupConfig = Field(default_factory=BackupConfig)
    drives: DrivesConfig = Field(default_factory=DrivesConfig)
    notion: NotionConfig = Field(default_factory=NotionConfig)
    gh: GhConfig = Field(default_factory=GhConfig)
    chrome: ChromeConfig = Field(default_factory=ChromeConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)


class CliSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLI_", extra="ignore")

    config_dir: Path = Field(default_factory=lambda: user_cli_config_dir())


def user_cli_config_dir() -> Path:
    """OS-standard user config directory (XDG on Linux, Application Support on macOS)."""
    return Path(user_config_dir("cli", appauthor=False))


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


def _deep_merge(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def active_config_profile() -> str | None:
    """Named overlay file config.<profile>.yaml (e.g. test)."""
    profile = os.environ.get("CLI_PROFILE", "").strip()
    if profile:
        return profile
    if os.environ.get("CLI_ENV", "").strip().lower() == "test":
        return "test"
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return "test"
    return None


def bundled_config_dir() -> Path:
    """Repo-shipped defaults for contributors and CI (not used at runtime unless CLI_CONFIG_DIR)."""
    return project_root() / "config"


def default_config_dir() -> Path:
    """User config dir; override with CLI_CONFIG_DIR (tests, Docker, custom installs)."""
    env = os.environ.get("CLI_CONFIG_DIR")
    if env:
        return Path(env).expanduser()
    return user_cli_config_dir()


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
    load_local_env()
    explicit_dir = bool(os.environ.get("CLI_CONFIG_DIR", "").strip())
    base = config_dir or default_config_dir()
    main_path = base / "config.yaml"
    drives_path = base / "drives.yaml"

    merged: dict = load_yaml(main_path) if main_path.is_file() else {}
    if not explicit_dir:
        profile = active_config_profile()
        if profile:
            profile_path = base / f"config.{profile}.yaml"
            if profile_path.is_file():
                merged = _deep_merge(merged, load_yaml(profile_path))

    drives_data = load_yaml(drives_path)
    if "drives" in drives_data:
        merged["drives"] = _normalize_drives(drives_data["drives"])

    auth_data = load_yaml(base / "auth.yaml")
    if auth_data:
        merged.update(auth_data)

    board_file = os.environ.get("CLI_BOARD_FILE", "").strip()
    if board_file:
        board_data = load_yaml(Path(board_file).expanduser())
        for key, value in board_data.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value

    return CliConfig.model_validate(merged)


def _credential_token(cfg: CliConfig, name: str, fallback_env: str) -> str | None:
    auth = getattr(cfg.auth, name)
    env_name = auth.env.strip() or fallback_env
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    raw_file = auth.token_file.strip()
    if not raw_file:
        return None
    path = Path(raw_file).expanduser()
    if not path.is_absolute():
        path = default_config_dir() / path
    if not path.is_file():
        return None
    token = path.read_text(encoding="utf-8").strip()
    return token or None


def tags_dir_path(config_dir: Path | None = None) -> Path:
    """Resolved absolute path to local tag zip storage."""
    cfg = load_config(config_dir)
    raw = cfg.backup.tags_dir.strip()
    if not raw:
        raise RuntimeError(
            "backup.tags_dir is not configured. "
            "Run `cli configure set backup.tags_dir <path>`."
        )
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (project_root() / path).resolve()


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


def chrome_profile_key(profile: str | None = None, config_dir: Path | None = None) -> str:
    """Resolve profile key from CLI flag or config default."""
    if profile and profile.strip():
        return profile.strip()
    return load_config(config_dir).chrome.profile.strip() or "Default"


def _resolve_bookmarks_raw(chrome: ChromeConfig, profile_key: str) -> str:
    if profile_key in chrome.profiles:
        profile_path = chrome.profiles[profile_key].bookmarks_file.strip()
        if profile_path:
            return profile_path
    if profile_key == (chrome.profile.strip() or "Default") or not chrome.profiles:
        return chrome.bookmarks_file.strip()
    raise FileNotFoundError(
        f"No chrome.bookmarks_file configured for profile {profile_key!r}. "
        "Add chrome.profiles.<name>.bookmarks_file or chrome.bookmarks_file in config."
    )


def bookmarks_file_path(profile: str | None = None, config_dir: Path | None = None) -> Path:
    """Resolved path for Chrome bookmarks HTML backup."""
    env = os.environ.get("CLI_BOOKMARKS_FILE")
    profile_key = chrome_profile_key(profile, config_dir)
    if env and profile is None:
        return Path(env).expanduser().resolve()
    cfg = load_config(config_dir)
    raw = _resolve_bookmarks_raw(cfg.chrome, profile_key)
    if not raw:
        raise FileNotFoundError(
            "chrome.bookmarks_file is not configured. Set chrome.bookmarks_file in config/config.yaml "
            f"or chrome.profiles.{profile_key}.bookmarks_file."
        )
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def chrome_snapshots_dir(config_dir: Path | None = None) -> Path | None:
    """Optional directory for timestamped bookmark snapshots."""
    raw = load_config(config_dir).chrome.snapshots_dir.strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def chrome_snapshot_retention(config_dir: Path | None = None) -> int:
    """Max snapshot files per profile (0 = unlimited)."""
    return max(0, load_config(config_dir).chrome.snapshot_retention)


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
    cfg = cfg or load_config()
    token = _credential_token(cfg, "notion", "NOTION_TOKEN")
    if not token:
        raise RuntimeError(
            "NOTION_TOKEN is not set. Export it or configure auth.notion.token_file."
        )
    notion_database_id(cfg.notion)
    return token


def backup_zip_password() -> str | None:
    """Zip encryption password from BACKUP_ZIP_PASSWORD (never commit to config)."""
    return _credential_token(load_config(), "backup", "BACKUP_ZIP_PASSWORD")


def require_backup_zip_password() -> str:
    password = backup_zip_password()
    if not password:
        raise RuntimeError(
            "BACKUP_ZIP_PASSWORD is not set. Export a zip password for encrypted "
            "backup repositories (see .env.example)."
        )
    return password


def require_google_drive_token(cfg: CliConfig | None = None) -> str:
    """Google Drive OAuth access token from GOOGLE_DRIVE_TOKEN (never commit to config)."""
    cfg = cfg or load_config()
    token = _credential_token(cfg, "google_drive", "GOOGLE_DRIVE_TOKEN")
    if not token:
        raise RuntimeError(
            "GOOGLE_DRIVE_TOKEN is not set. Export it or configure auth.google_drive.token_file."
        )
    return token


def require_onedrive_token(cfg: CliConfig | None = None) -> str:
    """OneDrive OAuth access token from ONEDRIVE_TOKEN (never commit to config)."""
    cfg = cfg or load_config()
    token = _credential_token(cfg, "onedrive", "ONEDRIVE_TOKEN")
    if not token:
        raise RuntimeError(
            "ONEDRIVE_TOKEN is not set. Export it or configure auth.onedrive.token_file."
        )
    return token


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


def photos_dir_path(config_dir: Path | None = None) -> Path:
    """Resolved private directory for ingested Google Photos albums."""
    env = os.environ.get("CLI_PHOTOS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    raw = load_config(config_dir).chrome.photos_dir.strip()
    if not raw:
        raise FileNotFoundError(
            "chrome.photos_dir is not configured. Set chrome.photos_dir in config/config.yaml "
            "or CLI_PHOTOS_DIR."
        )
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project_root() / path).resolve()


def photos_takeout_dir(config_dir: Path | None = None) -> Path:
    """Folder polled for newest Google Takeout .zip (defaults to chrome.downloads_dir)."""
    env = os.environ.get("CLI_PHOTOS_TAKEOUT_DIR")
    if env:
        return Path(env).expanduser().resolve()
    raw = load_config(config_dir).chrome.photos_takeout_dir.strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return chrome_downloads_dir(config_dir)


def tasks_link_repo(config_dir: Path | None = None) -> str:
    """GitHub owner/repo for task runbook links (git-hosted tasks/ tree)."""
    repo = load_config(config_dir).notion.link_repo.strip()
    if not repo:
        raise RuntimeError("notion.link_repo is not configured.")
    return repo


def task_runbook_url(body_filepath: str, *, config_dir: Path | None = None) -> str:
    """GitHub blob URL for a task body under the configured tasks repo."""
    cfg = load_config(config_dir)
    repo = tasks_link_repo(config_dir)
    branch = (cfg.notion.link_branch or "main").strip()
    rel = body_filepath.strip().lstrip("/")
    return f"https://github.com/{repo}/blob/{branch}/tasks/{rel}"


def notion_labels_manifest(config_dir: Path | None = None) -> Path:
    cfg = load_config(config_dir)
    raw = cfg.notion.labels_manifest.strip() or "labels.manifest.yaml"
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (notion_task_root(config_dir) / path).resolve()
