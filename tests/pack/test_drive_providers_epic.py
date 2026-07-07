"""Pack tests — Epic 04 drive providers (#12–#14) and download (#29)."""

from __future__ import annotations

from pathlib import Path

from tests.pack.conftest import requires_docs

ROOT = Path(__file__).resolve().parents[2]


def test_google_drive_provider_module() -> None:
    assert (ROOT / "src" / "providers" / "google_drive.py").is_file()
    assert (ROOT / "tests" / "providers" / "test_google_drive.py").is_file()


def test_onedrive_provider_module() -> None:
    assert (ROOT / "src" / "providers" / "onedrive.py").is_file()
    assert (ROOT / "tests" / "providers" / "test_onedrive.py").is_file()


def test_proton_drive_deferred_module() -> None:
    text = (ROOT / "src" / "providers" / "proton_drive.py").read_text(encoding="utf-8")
    assert "ProtonDriveUnsupportedError" in text
    assert (ROOT / "tests" / "providers" / "test_proton_drive.py").is_file()


def test_drive_download_command_registered() -> None:
    text = (ROOT / "src" / "commands" / "drive.py").read_text(encoding="utf-8")
    assert '@drive_app.command("download")' in text
    checks = (ROOT / "src" / "integration" / "cli_api_checks.py").read_text(encoding="utf-8")
    assert "drive download" in checks


@requires_docs
def test_drive_provider_docs() -> None:
    text = (ROOT / "docs" / "drive.md").read_text(encoding="utf-8")
    assert "GOOGLE_DRIVE_TOKEN" in text
    assert "ONEDRIVE_TOKEN" in text
    assert "Proton Drive is **deferred**" in text
    assert "Download semantics (#29)" in text
    assert "Tag backup automation (#15)" in text
