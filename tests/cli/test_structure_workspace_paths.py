from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app


runner = CliRunner()


def test_structure_workspace_paths_command_passes_for_existing_paths(tmp_path: Path) -> None:
    repo = tmp_path / "index"
    repo.mkdir()
    (repo / "README.md").write_text("# index\n", encoding="utf-8")
    manifest = tmp_path / "required-paths.txt"
    manifest.write_text("public/index\npublic/index/README.md\npublic/projects/cli\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "structure",
            "workspace-paths",
            "--manifest",
            str(manifest),
            "--workspace-root",
            str(tmp_path),
            "--base",
            "public/index",
            "--repo-root",
            str(repo),
        ],
    )

    assert result.exit_code == 0
    assert "checked 2, skipped 1" in result.stdout


def test_structure_workspace_paths_command_fails_for_missing_paths(tmp_path: Path) -> None:
    repo = tmp_path / "index"
    repo.mkdir()
    manifest = tmp_path / "required-paths.txt"
    manifest.write_text("public/index/README.md\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "structure",
            "workspace-paths",
            "--manifest",
            str(manifest),
            "--workspace-root",
            str(tmp_path),
            "--base",
            "public/index",
            "--repo-root",
            str(repo),
        ],
    )

    assert result.exit_code == 1
    assert "Required workspace path is missing: public/index/README.md" in result.stderr
