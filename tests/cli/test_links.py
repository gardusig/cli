from tests.constants import ROOT

"""cli links index command."""

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_links_lists_docs_and_defaults() -> None:
    result = runner.invoke(app, ["links"])
    assert result.exit_code == 0
    assert "Workflow shortcuts" in result.stdout
    assert "cli git push" in result.stdout
    assert "Quick defaults" in result.stdout
    assert "docs/large-files.md" in result.stdout
    assert "cli git start" in result.stdout
    assert "cli chrome bookmarks ingest" in result.stdout
    assert "wip-YYMMDD" in result.stdout


def test_root_help_mentions_links() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "links" in result.stdout


def test_links_lists_visible_top_level_commands() -> None:
    result = runner.invoke(app, ["links"])
    assert result.exit_code == 0
    visible_groups = {group.name for group in app.registered_groups if not group.hidden}
    for name in sorted(visible_groups):
        assert f"cli {name}" in result.stdout


def test_links_documents_restore_placeholder() -> None:
    result = runner.invoke(app, ["links"])
    assert result.exit_code == 0
    assert "restore" in result.stdout.lower()


def test_links_mentions_tasks_and_contest() -> None:
    result = runner.invoke(app, ["links"])
    assert result.exit_code == 0
    assert "cli tasks" in result.stdout
    assert "cli contest" in result.stdout
