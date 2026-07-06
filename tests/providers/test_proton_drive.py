"""Proton Drive deferral tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.providers import proton_drive
from src.providers.proton_drive import ProtonDriveUnsupportedError


@pytest.mark.parametrize(
    "fn,args",
    [
        (proton_drive.list_files, ("git-tags",)),
        (proton_drive.exists, ("git-tags/a.zip",)),
        (proton_drive.create_directory, ("git-tags",)),
        (proton_drive.upload, (Path("/a"), "git-tags/a.zip")),
        (proton_drive.download, ("git-tags/a.zip", "/tmp/a.zip")),
    ],
)
def test_proton_raises_clear_error(fn, args) -> None:
    with pytest.raises(ProtonDriveUnsupportedError, match="not supported"):
        fn(*args)
