"""Drive upload sync engine and internal helper tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.backup_repository import SyncResult
from src.services.drive_sync import _scan_local_files, sync_all, upload_missing
from tests.harness.drive_harness import InMemoryDriveProvider


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.files: set[str] = set()
        self.dirs: set[str] = set()

    def list_files(self, root: str) -> set[str]:
        root = root.strip("/")
        out: set[str] = set()
        for path in self.files:
            if root and path.startswith(root + "/"):
                out.add(path[len(root) + 1 :])
            elif not root:
                out.add(path)
        return out

    def exists(self, path: str) -> bool:
        return path in self.files

    def create_directory(self, path: str) -> None:
        self.dirs.add(path)

    def upload(self, local: Path, remote: str) -> None:
        self.files.add(remote)


def test_plan_ingest_repositories_reports_missing_tags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.services.backup_repository import plan_ingest_repositories

    repo = tmp_path / "demo"
    repo.mkdir()
    (repo / ".git").mkdir()
    tags_root = tmp_path / "git-tags" / "demo"
    tags_root.mkdir(parents=True)
    (tags_root / "demo-v1.0.0.zip").write_bytes(b"z")

    monkeypatch.setattr(
        "src.services.backup_repository.load_config",
        lambda config_dir=None: type(
            "Cfg",
            (),
            {
                "backup": type(
                    "Backup",
                    (),
                    {"repositories": [type("Entry", (), {"path": str(repo)})()]},
                )()
            },
        )(),
    )
    monkeypatch.setattr(
        "src.services.backup_repository.list_git_tags",
        lambda _repo: ["v1.0.0", "v2.0.0"],
    )
    monkeypatch.setattr(
        "src.services.backup_repository.list_downloaded_tags",
        lambda _repo, config_dir=None: ["v1.0.0"],
    )
    rows = plan_ingest_repositories()
    assert rows[0][1].created == ["v2.0.0"]
    assert rows[0][1].replaced == ["v1.0.0"]


def test_sync_all_dry_run_plans_without_ingest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    calls = {"plan": 0, "ingest": 0}

    def _plan(_path: str | None = None) -> list[tuple[Path, SyncResult]]:
        calls["plan"] += 1
        return []

    def _ingest(_path: str | None = None) -> list[tuple[Path, SyncResult]]:
        calls["ingest"] += 1
        return []

    monkeypatch.setattr("src.services.drive_sync.plan_ingest_repositories", _plan)
    monkeypatch.setattr("src.services.drive_sync.ingest_repositories", _ingest)
    result = sync_all(tags_root, [], dry_run=True)
    assert result.dry_run is True
    assert calls["plan"] == 1
    assert calls["ingest"] == 0


def test_sync_all_ingests_then_uploads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repos" / "demo"
    repo.mkdir(parents=True)
    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    (tags_root / "demo").mkdir()
    (tags_root / "demo" / "v1.zip").write_bytes(b"z")

    monkeypatch.setattr(
        "src.services.drive_sync.ingest_repositories",
        lambda _path=None: [(repo, SyncResult(created=["v1"], replaced=[], failed=[]))],
    )
    provider = FakeProvider()
    result = sync_all(tags_root, [("fake", provider, "remote")])
    assert len(result.ingest) == 1
    assert result.uploads[0][0] == "fake"
    assert "demo/v1.zip" in result.uploads[0][1].uploaded


def test_upload_missing_skips_existing(tmp_path: Path) -> None:
    local = tmp_path / "tag-folder" / "repo"
    local.mkdir(parents=True)
    (local / "a.zip").write_bytes(b"a")
    (local / "b.zip").write_bytes(b"b")
    provider = FakeProvider()
    provider.files.add("Backups/tag-folder/repo/a.zip")
    result = upload_missing(tmp_path / "tag-folder", provider, "Backups/tag-folder")
    assert "repo/a.zip" in result.skipped
    assert "repo/b.zip" in result.uploaded


def test_scan_local_files_empty_when_missing(tmp_path: Path) -> None:
    assert _scan_local_files(tmp_path / "missing") == []


def test_scan_local_files_returns_posix_relative_paths(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.txt").write_text("1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    assert _scan_local_files(tmp_path) == ["a/one.txt", "b.txt"]


def test_upload_missing_dry_run_skips_writes(tmp_path: Path) -> None:
    local = tmp_path / "hub" / "repo"
    local.mkdir(parents=True)
    (local / "a.zip").write_bytes(b"a")
    provider = FakeProvider()
    result = upload_missing(tmp_path / "hub", provider, "remote", dry_run=True)
    assert "repo/a.zip" in result.uploaded
    assert not provider.files


def test_upload_missing_continues_after_file_error(tmp_path: Path) -> None:
    local = tmp_path / "hub" / "repo"
    local.mkdir(parents=True)
    (local / "a.zip").write_bytes(b"a")
    (local / "b.zip").write_bytes(b"b")

    class PartialFailProvider(FakeProvider):
        def upload(self, local_path: Path, remote: str) -> None:
            if local_path.name == "a.zip":
                raise RuntimeError("upload failed")
            super().upload(local_path, remote)

    result = upload_missing(tmp_path / "hub", PartialFailProvider(), "remote")
    assert any(rel == "repo/a.zip" for rel, _ in result.failed)
    assert "repo/b.zip" in result.uploaded

    class BrokenProvider(InMemoryDriveProvider):
        def list_files(self, prefix: str) -> list[str]:
            raise RuntimeError("cloud down")

    result = upload_missing(tmp_path, BrokenProvider(), "remote")
    assert result.failed
    assert "cloud down" in result.failed[0][1]
