from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.services.toolkit.catalog import command_spec
from src.services.toolkit.detect import ToolkitDetectionError, confirm_markers, repo_languages
from src.services.toolkit.runner import run_cli_command


def test_catalog_maps_command_to_python_handler() -> None:
    spec = command_spec("lint", "java")
    assert spec.handler == "lint_java"
    assert spec.requires_bins == ("java", "javac")


def test_confirm_markers_rejects_wrong_language(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ToolkitDetectionError, match="missing one of"):
        confirm_markers(tmp_path, ("pom.xml", "build.gradle"))


def test_repo_languages_uses_known_profile_when_markers_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "python-cli"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (root / "README.md").write_text("# hi\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "x.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 1, "", ""))
    assert repo_languages(root) == ("markdown", "python", "shell")


def test_repo_languages_uses_pyproject_profile_without_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "gardusig-cli"\n', encoding="utf-8")
    (root / "README.md").write_text("# hi\n", encoding="utf-8")
    (root / "main.py").write_text("print(1)\n", encoding="utf-8")
    fixtures = root / "tests" / "fixtures" / "contest" / "toy"
    fixtures.mkdir(parents=True)
    (fixtures / "solution.cpp").write_text("int main() {}\n", encoding="utf-8")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 1, "", ""))
    assert repo_languages(root) == ("markdown", "python")


def test_runner_invokes_related_python_handler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pom.xml").write_text("<project />\n", encoding="utf-8")
    seen: dict[str, object] = {}
    monkeypatch.setattr("src.services.toolkit.prereqs.shutil.which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen["cmd"] = cmd
        seen["cwd"] = kwargs["cwd"]
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run_cli_command("test", "java", tmp_path, suite="unit") == 0
    assert seen["cmd"] == ["mvn", "-q", "test"]
    assert seen["cwd"] == tmp_path.resolve()

