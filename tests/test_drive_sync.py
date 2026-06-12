"""Drive upload sync engine tests."""

from __future__ import annotations

from pathlib import Path

from shuttle.services.backup_repository import SyncResult
from shuttle.services.drive_sync import sync_all, upload_missing


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


def test_sync_all_ingests_then_uploads(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repos" / "demo"
    repo.mkdir(parents=True)
    tags_root = tmp_path / "git-tags"
    tags_root.mkdir()
    (tags_root / "demo").mkdir()
    (tags_root / "demo" / "v1.zip").write_bytes(b"z")

    monkeypatch.setattr(
        "shuttle.services.drive_sync.ingest_repositories",
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
