"""Deploy readiness — main vs latest tag and open PR gate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli import app
from src.services.git_deploy import DeployAssessment, assess_deploy_readiness

runner = CliRunner()


def _assessment(
    *,
    needs_tag: bool = True,
    open_prs: tuple[dict[str, object], ...] = (),
    suggested: str = "v0.1.1",
    latest: str | None = "v0.1.0",
) -> DeployAssessment:
    return DeployAssessment(
        repo="gardusig/cli",
        main_sha="a" * 40,
        latest_tag=latest,
        tag_sha="b" * 40 if latest else None,
        needs_tag=needs_tag,
        suggested_tag=suggested if needs_tag else None,
        open_prs=open_prs,
    )


@patch("src.commands.git.assess_deploy_readiness")
def test_git_deploy_status_read_only(mock_assess: MagicMock) -> None:
    mock_assess.return_value = _assessment()
    result = runner.invoke(app, ["git", "deploy", "--status"])
    assert result.exit_code == 0
    assert "needs_tag: yes" in result.stdout


@patch("src.commands.git.assess_deploy_readiness")
def test_git_deploy_blocked_by_open_pr(mock_assess: MagicMock) -> None:
    mock_assess.return_value = _assessment(
        open_prs=({"number": 86, "title": "WIP"},),
    )
    result = runner.invoke(app, ["git", "deploy", "--yes"])
    assert result.exit_code == 1
    assert "blocked" in result.stdout


@patch("src.commands.git._tag_create")
@patch("src.commands.git.assess_deploy_readiness")
def test_git_deploy_skips_when_main_matches_tag(
    mock_assess: MagicMock,
    mock_tag: MagicMock,
) -> None:
    mock_assess.return_value = _assessment(needs_tag=False, suggested=None)
    result = runner.invoke(app, ["git", "deploy", "--yes"])
    assert result.exit_code == 0
    assert "skip" in result.stdout
    mock_tag.assert_not_called()


@patch("src.commands.git._tag_create")
@patch("src.commands.git.assess_deploy_readiness")
def test_git_deploy_tags_when_ready(mock_assess: MagicMock, mock_tag: MagicMock) -> None:
    mock_assess.return_value = _assessment()
    result = runner.invoke(app, ["git", "deploy", "--yes"])
    assert result.exit_code == 0
    assert "deployed" in result.stdout
    mock_tag.assert_called_once_with(None, yes=True)


def test_assess_deploy_readiness_needs_tag_when_main_ahead(tmp_path: Path) -> None:
    svc = MagicMock()
    svc.fetch_all.return_value = None
    svc.main_tip_sha.return_value = "mainsha"
    svc.all_tag_names.return_value = ["v0.1.0"]
    svc.tag_remote_sha.return_value = "oldsha"
    svc.tag_local_sha.return_value = "oldsha"
    svc.top = str(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "tag.yaml").write_text(
        "pattern: semver-v\nbump: patch\nrequire_increase: true\n",
        encoding="utf-8",
    )
    gh = MagicMock()
    gh.repo_display.return_value = "gardusig/cli"
    gh.pr_list.return_value = []

    assessment = assess_deploy_readiness(svc, repo_root=tmp_path, gh_svc=gh, fetch=False)
    assert assessment.needs_tag is True
    assert assessment.suggested_tag == "v0.1.1"
    assert assessment.open_pr_count == 0


def test_assess_deploy_readiness_skip_when_main_matches_tag(tmp_path: Path) -> None:
    svc = MagicMock()
    svc.main_tip_sha.return_value = "same"
    svc.all_tag_names.return_value = ["v0.1.0"]
    svc.tag_remote_sha.return_value = "same"
    svc.tag_local_sha.return_value = "same"
    svc.top = str(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "tag.yaml").write_text("pattern: semver-v\n", encoding="utf-8")

    assessment = assess_deploy_readiness(svc, repo_root=tmp_path, gh_svc=None, fetch=False)
    assert assessment.needs_tag is False


def test_assess_deploy_readiness_plain_pattern_first_tag(tmp_path: Path) -> None:
    svc = MagicMock()
    svc.main_tip_sha.return_value = "mainsha"
    svc.all_tag_names.return_value = []
    svc.top = str(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "tag.yaml").write_text("pattern: date\n", encoding="utf-8")

    assessment = assess_deploy_readiness(svc, repo_root=tmp_path, gh_svc=None, fetch=False)
    assert assessment.needs_tag is True
    assert assessment.suggested_tag is not None
    assert len(assessment.suggested_tag) == 10
