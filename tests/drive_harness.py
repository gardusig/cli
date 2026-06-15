"""Drive provider mocks for integration tests."""

from __future__ import annotations

from pathlib import Path

from shuttle.providers.base import DriveProvider


class InMemoryDriveProvider(DriveProvider):
    """Minimal DriveProvider that stores uploaded remote paths in memory."""

    name = "memory"

    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str]] = []
        self._remote_paths: set[str] = set()

    def upload(self, local_path: Path, remote_path: str) -> None:
        self.uploaded.append((str(local_path), remote_path))
        self._remote_paths.add(remote_path.replace("\\", "/"))

    def download(self, remote_path: str, local_path: str) -> None:
        raise NotImplementedError

    def list_files(self, prefix: str) -> list[str]:
        prefix = prefix.strip("/")
        rels: list[str] = []
        needle = f"{prefix}/" if prefix else ""
        for remote in sorted(self._remote_paths):
            if prefix and remote.startswith(needle):
                rels.append(remote[len(needle) :])
            elif not prefix:
                rels.append(remote.rsplit("/", 1)[-1])
        return rels

    def exists(self, remote_path: str) -> bool:
        return remote_path.replace("\\", "/") in self._remote_paths

    def create_directory(self, remote_path: str) -> None:
        return None

    def delete(self, remote_path: str) -> None:
        self._remote_paths.discard(remote_path.replace("\\", "/"))


class DriveRemoteError(RuntimeError):
    """Drive provider failure; set retryable=True for transient errors."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class FailingDriveProvider(InMemoryDriveProvider):
    """DriveProvider that fails on a chosen operation (optionally after N successes)."""

    name = "drive"

    def __init__(
        self,
        *,
        operation: str = "list_files",
        error: DriveRemoteError | None = None,
        failures_before_ok: int = 0,
    ) -> None:
        super().__init__()
        self._operation = operation
        self._error = error or DriveRemoteError("remote drive unavailable")
        self._failures_before_ok = failures_before_ok
        self._attempts = 0

    def _maybe_fail(self, operation: str) -> None:
        if operation != self._operation:
            return
        if self._attempts < self._failures_before_ok:
            self._attempts += 1
            raise self._error
        self._attempts += 1

    def list_files(self, prefix: str) -> list[str]:
        self._maybe_fail("list_files")
        return super().list_files(prefix)

    def exists(self, remote_path: str) -> bool:
        self._maybe_fail("exists")
        return super().exists(remote_path)

    def upload(self, local_path: Path, remote_path: str) -> None:
        self._maybe_fail("upload")
        super().upload(local_path, remote_path)

    def create_directory(self, remote_path: str) -> None:
        self._maybe_fail("create_directory")
        super().create_directory(remote_path)
