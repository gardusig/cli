"""Runtime profile — laptop vs container; optional integrations."""

from __future__ import annotations

import os
from enum import Enum


class RuntimeProfile(str, Enum):
    LAPTOP = "laptop"
    CONTAINER = "container"
    CI = "ci"


def detect_profile() -> RuntimeProfile:
    if os.environ.get("CLI_RUNTIME") == "container":
        return RuntimeProfile.CONTAINER
    if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"):
        return RuntimeProfile.CI
    return RuntimeProfile.LAPTOP


def is_headless() -> bool:
    return detect_profile() in {RuntimeProfile.CONTAINER, RuntimeProfile.CI}


def notion_configured() -> bool:
    if os.environ.get("CLI_SKIP_NOTION") == "1":
        return False
    try:
        from src.utils.config import load_config

        cfg = load_config()
        return bool(cfg.notion.database_id and os.environ.get("NOTION_TOKEN"))
    except Exception:
        return False


def optional_integration(name: str) -> bool:
    if os.environ.get(f"CLI_SKIP_{name.upper()}") == "1":
        return False
    if name == "notion":
        return notion_configured()
    return True
