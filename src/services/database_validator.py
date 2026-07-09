"""Validation rules for gardusig/private."""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import yaml

FINANCE_RE = re.compile(r"(^|/)finance(/|$)|^work-proof/")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if text.startswith("#"):
        text = "\n".join(line for line in text.splitlines() if not line.startswith("# "))
    data = yaml.safe_load(text) or {}
    return data if isinstance(data, dict) else {}


def _parse_date(value: object) -> date | None:
    if value is None or value == "" or str(value).lower() == "null":
        return None
    return date.fromisoformat(str(value))


def _deleted_files(root: Path, base: str) -> list[str]:
    ref = base if base.startswith(("origin/", "refs/")) else f"origin/{base}"
    branch = ref.removeprefix("origin/")
    subprocess.run(["git", "fetch", "origin", branch], cwd=root, capture_output=True)
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", ref],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=D", merge_base, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def validate_database_repo(root: Path, *, base: str = "main") -> tuple[list[str], list[str]]:
    root = root.expanduser().resolve()
    catalog = root / "catalog"
    tasks = root / "tasks"
    files_data = _load_yaml(catalog / "files.yaml")
    docs_data = _load_yaml(catalog / "documents.yaml")
    manifest_files: list[str] = list(files_data.get("files") or [])
    directories: list[str] = list(files_data.get("directories") or [])
    documents: list[dict[str, Any]] = list(docs_data.get("documents") or [])

    errors: list[str] = []
    warnings: list[str] = []
    for key in ("version", "generated", "directories", "files"):
        if key not in files_data:
            errors.append(f"files.yaml missing key: {key}")
    for dirname in ("brazil/", "canada/", "health/", "work-proof/"):
        if dirname not in directories and not (root / dirname.rstrip("/")).is_dir():
            errors.append(f"Missing top-level folder: {dirname}")
    for rel in manifest_files:
        if not (root / rel).is_file():
            errors.append(f"Missing catalog file: {rel}")
    manifest_set = set(manifest_files)
    for deleted in _deleted_files(root, base):
        if deleted.startswith(("catalog/", "scripts/", ".github/")):
            continue
        errors.append(f"PR deletes file (not allowed): {deleted}")
        if deleted in manifest_set:
            errors.append("  -> path is in catalog/files.yaml")

    today = date.today()
    seen: set[str] = set()
    for doc in documents:
        doc_id = doc.get("id") or doc.get("filepath", "?")
        fp = doc.get("filepath")
        if not fp:
            errors.append(f"document {doc_id}: missing filepath")
            continue
        if fp in seen:
            errors.append(f"duplicate document filepath: {fp}")
        seen.add(str(fp))
        if FINANCE_RE.search(str(fp)):
            errors.append(f"document {doc_id}: finance/work-proof paths belong outside documents.yaml ({fp})")
            continue
        if not (root / str(fp)).is_file():
            errors.append(f"document {doc_id}: file not found: {fp}")
        issued = _parse_date(doc.get("issued_at"))
        expires = _parse_date(doc.get("expires_on"))
        required_until = _parse_date(doc.get("required_until"))
        if issued and expires and issued > expires:
            errors.append(f"document {doc_id}: issued_at after expires_on")
        if required_until and required_until < today:
            warnings.append(f"document {doc_id}: required_until {required_until} passed")
        elif expires and expires < today:
            warnings.append(f"document {doc_id}: expires_on {expires} passed")

    manifest = tasks / "tasks.pairs.json"
    if tasks.exists() and not manifest.is_file():
        errors.append("tasks/tasks.pairs.json missing")
    return errors, warnings
