"""Tests for selective pipeline job expansion."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.services.pipeline_selective import apply_selective_jobs


def _base_jobs() -> dict[str, dict]:
    return {
        "lint": {"id": "lint", "target": "lint"},
        "repo-hygiene": {"id": "repo-hygiene", "target": "repo-hygiene", "needs": "lint"},
        "version-check": {"id": "version-check", "target": "version-check", "needs": "repo-hygiene"},
        "core-gates": {"id": "core-gates", "target": "core-gates", "needs": "version-check"},
        "package-unit": {
            "id": "package-unit",
            "name": "Unit",
            "target": "package-unit",
            "matrix": "unit",
            "needs": "core-gates",
        },
        "package-integration": {
            "id": "package-integration",
            "name": "Integration",
            "target": "package-integration",
            "matrix": "integration",
            "needs": "core-gates",
        },
        "unit": {
            "id": "unit",
            "target": "unit-test",
            "when_full_suite": True,
            "needs": "version-check",
        },
        "integration": {
            "id": "integration",
            "target": "integration-test",
            "when_full_suite": True,
            "docker_socket": True,
            "needs": "unit",
        },
        "pypi": {"id": "pypi", "target": "pypi-test", "needs": "unit"},
        "testpypi-consumer": {
            "id": "testpypi-consumer",
            "target": "testpypi-consumer",
            "needs": "pypi",
        },
    }


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "src" / "commands").mkdir(parents=True)
    (tmp_path / "src" / "commands" / "gh.py").write_text("# gh\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "src" / "commands" / "gh.py").write_text("# gh change\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feature"], cwd=tmp_path, check=True, capture_output=True)


def test_apply_selective_jobs_expands_package_matrix(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    jobs = apply_selective_jobs(
        _base_jobs(),
        cfg={"selective": True},
        app_src=tmp_path,
        selective_base="main",
        selective_head="feature",
    )
    assert "unit-gh" in jobs
    assert jobs["unit-gh"]["build_args"]["PACKAGE"] == "gh"
    assert "integration-gh" in jobs
    assert "test-gate" in jobs
    assert "integration-gh" in jobs["test-gate"]["needs"]
    assert jobs["pypi"]["needs"] == ["test-gate"]
    assert "unit" not in jobs


def test_apply_selective_jobs_falls_back_to_full_suite(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "src" / "cli.py").write_text("# broad\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "cli"], cwd=tmp_path, check=True, capture_output=True)
    jobs = apply_selective_jobs(
        _base_jobs(),
        cfg={"selective": True},
        app_src=tmp_path,
        selective_base="main",
        selective_head="feature",
    )
    assert "unit-gh" not in jobs
    assert "unit" in jobs
    assert "integration" in jobs
    assert jobs["pypi"]["needs"] == ["unit"]


def test_apply_selective_jobs_skips_without_selective_flag(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    jobs = apply_selective_jobs(
        _base_jobs(),
        cfg={},
        app_src=tmp_path,
        selective_base="main",
        selective_head="feature",
    )
    assert jobs == _base_jobs()
