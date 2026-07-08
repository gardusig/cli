from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
import yaml

from src.services.pipeline_runtime import resolve_config


def test_pipeline_config_resolve_stages_jobs(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "demo.yaml").write_text(
        "\n".join(
            [
                "repo: gardusig/demo",
                "dockerfile: docker/demo.dockerfile",
                "jobs:",
                "  - id: lint",
                "    target: lint",
                "  - id: unit",
                "    target: unit-test",
                "    needs: lint",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=tmp_path,
            repo_slug="demo",
            pipeline="",
            repository="gardusig/demo",
            ref="feature",
            sha="abc123",
            job="",
            action="",
            dry_run="",
        )
    )

    values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
    assert values["repo_slug"] == "demo"
    assert values["checkout_ref"] == "abc123"
    assert values["has_stage_0"] == "true"
    assert values["has_stage_1"] == "true"
    stage_0 = json.loads(values["stage_0"])
    assert stage_0["include"][0]["job"]["id"] == "lint"


def test_pipeline_config_resolve_treats_null_client_as_empty(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "demo.yaml").write_text(
        "repo: gardusig/demo\ndockerfile: docker/demo.dockerfile\njobs:\n  - id: lint\n    target: lint\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "null")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=tmp_path,
            repo_slug="demo",
            pipeline="",
            repository="gardusig/demo",
            ref="feature",
            sha="abc123",
            job="",
            action="",
            dry_run="",
        )
    )

    assert "repo_slug=demo" in output.read_text(encoding="utf-8")


def test_pipeline_config_resolve_accepts_renamed_cli_repository(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "python-cli.yaml").write_text(
        "repo: gardusig/python-cli\ndockerfile: docker/python-cli.dockerfile\njobs:\n  - id: lint\n    target: lint\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=tmp_path,
            repo_slug="python-cli",
            pipeline="",
            repository="gardusig/cli",
            ref="feat/epic-06d-release",
            sha="abc123",
            job="",
            action="",
            dry_run="",
        )
    )

    assert "repo_slug=python-cli" in output.read_text(encoding="utf-8")


def test_pipeline_config_resolve_prefers_flattened_pipeline_config(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "cpp-compile.yaml").write_text(
        "repo: gardusig/cpp\ndockerfile: docker/cpp.dockerfile\njobs:\n  - id: lint\n    target: lint\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=tmp_path,
            repo_slug="cpp",
            pipeline="compile",
            repository="gardusig/cpp",
            ref="main",
            sha="",
            job="",
            action="",
            dry_run="",
        )
    )

    assert "config=" + str(cfg_dir / "cpp-compile.yaml") in output.read_text(encoding="utf-8")


def test_pipeline_config_resolve_prefers_app_repo_config(tmp_path: Path, monkeypatch) -> None:
    pipeline_src = tmp_path / "pipeline-src"
    cfg_dir = pipeline_src / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "demo.yaml").write_text(
        "repo: gardusig/demo\ndockerfile: docker/demo-central.dockerfile\njobs:\n  - id: lint\n    target: lint\n",
        encoding="utf-8",
    )
    app_src = tmp_path / "app-src"
    (app_src / ".github" / "workflows").mkdir(parents=True)
    (app_src / ".github" / "workflows" / "pull-request.yaml").write_text(
        "repo: gardusig/demo\ndockerfile: docker/demo-local.dockerfile\njobs:\n  - id: unit\n    target: unit-test\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=pipeline_src,
            app_src=app_src,
            repo_slug="demo",
            pipeline="",
            repository="gardusig/demo",
            ref="feature",
            sha="abc123",
            job="",
            action="",
            dry_run="",
        )
    )

    values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
    assert values["config"] == str(app_src / ".github" / "workflows" / "pull-request.yaml")
    stage_0 = json.loads(values["stage_0"])
    assert stage_0["include"][0]["job"]["id"] == "unit"


def test_pipeline_release_resolve_prefers_app_repo_config(tmp_path: Path, monkeypatch) -> None:
    pipeline_src = tmp_path / "pipeline-src"
    hub_cfg = pipeline_src / ".github" / "workflows" / "release"
    hub_cfg.mkdir(parents=True)
    (hub_cfg / "cli.yaml").write_text(
        "repo: gardusig/cli\ndockerfile: hub.dockerfile\njobs:\n  - id: release\n    target: release\n",
        encoding="utf-8",
    )
    app_src = tmp_path / "app-src"
    (app_src / ".github" / "workflows").mkdir(parents=True)
    (app_src / ".github" / "workflows" / "release.yaml").write_text(
        "repo: gardusig/cli\ndockerfile: Dockerfile\njobs:\n"
        "  - id: release\n    target: release\n"
        "  - id: pypi-consumer\n    target: pypi-consumer\n    needs: release\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="release",
            pipeline_src=pipeline_src,
            app_src=app_src,
            repo_slug="cli",
            pipeline="",
            repository="gardusig/cli",
            ref="refs/tags/v1.0.3",
            sha="",
            job="",
            action="",
            dry_run="",
        )
    )

    values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
    assert values["config"] == str(app_src / ".github" / "workflows" / "release.yaml")
    assert values["version"] == "1.0.3"
    stage_0 = json.loads(values["stage_0"])
    assert stage_0["include"][0]["job"]["id"] == "release"
    assert values["has_stage_1"] == "true"
    stage_1 = json.loads(values["stage_1"])
    assert stage_1["include"][0]["job"]["id"] == "pypi-consumer"


@pytest.mark.integration
def test_pull_request_configs_declare_inline_hygiene_policies() -> None:
    github_roots = [
        Path(__file__).resolve().parents[3],
        Path(__file__).resolve().parents[3].parent / "private",
    ]
    configs: list[Path] = []
    for github_root in github_roots:
        if not github_root.is_dir():
            continue
        for repo_root in sorted(github_root.iterdir()):
            if not repo_root.is_dir():
                continue
            for config_name in ("pull-request.yaml",):
                config = repo_root / ".github" / "workflows" / config_name
                if not config.is_file():
                    config = repo_root / ".github" / config_name
                if config.is_file():
                    configs.append(config)
    if not configs:
        pytest.skip("no app-repo pull-request configs found locally")

    for config in configs:
        data = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        jobs = data.get("jobs") or []
        policy_jobs = [job for job in jobs if isinstance(job, dict) and job.get("id") == "repo-hygiene"]
        assert policy_jobs, f"{config} missing repo-hygiene"
        policy = policy_jobs[0].get("hygiene_policy") or {}
        for key in ("allowed_root_dirs", "allowed_root_files", "allowed_extensions"):
            assert policy.get(key) is not None, f"{config} missing {key}"
        assert ".sh" in (policy.get("forbidden_extensions") or []), config
        if data.get("repo") == "gardusig/database":
            assert ".md" not in (policy.get("allowed_extensions") or []), config
