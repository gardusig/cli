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


def test_pipeline_config_resolve_prefers_flattened_pipeline_config(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "interviewing-cpp.yaml").write_text(
        "repo: gardusig/interviewing\ndockerfile: docker/cpp.dockerfile\njobs:\n  - id: lint\n    target: lint\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=tmp_path,
            repo_slug="interviewing",
            pipeline="cpp",
            repository="gardusig/interviewing",
            ref="main",
            sha="",
            job="",
            action="",
            dry_run="",
        )
    )

    assert "config=" + str(cfg_dir / "interviewing-cpp.yaml") in output.read_text(encoding="utf-8")


@pytest.mark.integration
def test_pull_request_configs_declare_inline_hygiene_policies() -> None:
    pipelines_root = Path(__file__).resolve().parents[3] / "github-pipelines"
    cfg_dir = pipelines_root / ".github" / "workflows" / "pull-request"
    if not cfg_dir.is_dir():
        pytest.skip("github-pipelines sibling checkout is not available")

    configs = sorted(cfg_dir.glob("*.yaml"))
    assert configs
    for config in configs:
        data = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        jobs = data.get("jobs") or []
        policy_jobs = [job for job in jobs if isinstance(job, dict) and job.get("id") == "repo-hygiene"]
        assert policy_jobs, f"{config.name} missing repo-hygiene"
        policy = policy_jobs[0].get("hygiene_policy") or {}
        for key in ("allowed_root_dirs", "allowed_root_files", "allowed_extensions"):
            assert policy.get(key) is not None, f"{config.name} missing {key}"
        assert ".sh" in (policy.get("forbidden_extensions") or []), config.name
        if data.get("repo") == "gardusig/database":
            assert ".md" not in (policy.get("allowed_extensions") or []), config.name
