"""Drive provider adapter with retry + user-facing errors."""

from __future__ import annotations

from pathlib import Path

from gardusig_cli.providers.base import DriveProvider
from gardusig_cli.utils.external_client import ExternalClient


class RetryingDriveProvider:
    """Wrap a DriveProvider so remote calls retry then fail with ExternalCallError."""

    def __init__(
        self,
        provider: DriveProvider,
        *,
        service_name: str | None = None,
        client: ExternalClient | None = None,
    ) -> None:
        self._provider = provider
        self._service = service_name or getattr(provider, "name", "drive")
        self._client = client or ExternalClient(self._service)

    @property
    def name(self) -> str:
        return self._service

    def list_files(self, root: str) -> list[str]:
        raw = self._client.call(
            "list files",
            lambda: self._provider.list_files(root),
        )
        if isinstance(raw, set):
            return sorted(raw)
        return list(raw)

    def exists(self, path: str) -> bool:
        return self._client.call("check remote file", lambda: self._provider.exists(path))

    def create_directory(self, path: str) -> None:
        self._client.call("create remote directory", lambda: self._provider.create_directory(path))

    def upload(self, local: Path, remote: str) -> None:
        self._client.call(
            f"upload {local.name}",
            lambda: self._provider.upload(local, remote),
        )


def wrap_drive_provider(
    provider: DriveProvider,
    *,
    service_name: str | None = None,
) -> RetryingDriveProvider:
    return RetryingDriveProvider(provider, service_name=service_name)
