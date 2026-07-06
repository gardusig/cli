from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def test_pipeline_config_resolve_prefers_flattened_pipeline_config(tmp_path: Path, monkeypatch) -> None:
    cfg_dir = tmp_path / ".github" / "workflows" / "pull-request"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "computer-science-cpp.yaml").write_text(
        "repo: gardusig/computer-science\ndockerfile: docker/cpp.dockerfile\njobs:\n  - id: lint\n    target: lint\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CLIENT", "{}")

    resolve_config(
        argparse.Namespace(
            family="pull-request",
            pipeline_src=tmp_path,
            repo_slug="computer-science",
            pipeline="cpp",
            repository="gardusig/computer-science",
            ref="main",
            sha="",
            job="",
            action="",
            dry_run="",
        )
    )

    assert "config=" + str(cfg_dir / "computer-science-cpp.yaml") in output.read_text(encoding="utf-8")
