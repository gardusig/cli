"""Notion task pair models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, field_validator


class TaskMetadata(BaseModel):
    """Metadata/*.yaml — name is the unique Notion title; body has no title heading."""

    name: str
    priority: int | None = None
    tag: str | None = None
    frequency: str | None = None
    interval: int | None = None
    last_done: str | None = None
    forced_status: str | None = None
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("task name must not be empty")
        return stripped

    @field_validator("priority", "interval", mode="before")
    @classmethod
    def _coerce_int(cls, value: object) -> int | None:
        if value is None or value == "":
            return None
        return int(value)


class TaskPair(BaseModel):
    """One manifest row: parallel metadata/body paths (name lives in metadata yaml)."""

    metadata_filepath: str
    body_filepath: str
    # Legacy manifest keys (ignored; name is read from metadata).
    id: str | None = None
    name: str | None = None

    def metadata_path(self, task_root: Path) -> Path:
        return task_root / self.metadata_filepath

    def body_path(self, task_root: Path) -> Path:
        return task_root / self.body_filepath


class ResolvedTaskPair(BaseModel):
    """Loaded pair with parsed metadata and body text."""

    pair: TaskPair
    metadata: TaskMetadata
    body: str = ""


@dataclass
class PairScanResult:
    """Complete pairs plus non-fatal orphan warnings."""

    pairs: list[TaskPair] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
