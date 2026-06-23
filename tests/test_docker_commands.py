"""CLI tests for cli docker commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.cli import app
from cli.services.docker_runtime import (
    ContainerRow,
    ContainerStatsRow,
    ImageRow,
    ResetSummary,
)

runner = CliRunner()


@patch("cli.commands.docker.docker_available", return_value=False)
def test_docker_ps_requires_binary(_avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "ps"])
    assert result.exit_code != 0
    assert "PATH" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_containers",
    return_value=[
        ContainerRow("abc", "/web", "running", 2048, 4096),
    ],
)
def test_docker_ps_lists_running(mock_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "ps"])
    assert result.exit_code == 0
    assert "web" in result.stdout
    mock_list.assert_called_once_with(running_only=True)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_container_stats",
    return_value=[
        ContainerStatsRow("abc", "web", 12.5, 50_000_000, 2_000_000_000, 2.4),
    ],
)
def test_docker_stats_cpu(mock_stats: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "stats", "--by", "cpu"])
    assert result.exit_code == 0
    assert "web" in result.stdout
    assert "12.5%" in result.stdout
    mock_stats.assert_called_once()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_images",
    return_value=[ImageRow("sha", "app", "latest", 1_000_000)],
)
def test_docker_images(mock_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "images", "--top", "5"])
    assert result.exit_code == 0
    assert "app:latest" in result.stdout
    mock_list.assert_called_once()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_images", return_value=[])
@patch(
    "cli.commands.docker.list_container_stats",
    return_value=[ContainerStatsRow("a", "run", 1.0, 100, 1000, 10.0)],
)
@patch(
    "cli.commands.docker.list_containers",
    side_effect=[
        [ContainerRow("b", "/stop", "exited", 300, 400)],
    ],
)
def test_docker_top(mock_list: MagicMock, _stats: MagicMock, _images: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "top", "-n", "1"])
    assert result.exit_code == 0
    assert "CPU" in result.stdout
    assert "run" in result.stdout
    mock_list.assert_called_once_with(all_containers=True)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.stop_containers")
@patch(
    "cli.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_stop_requires_yes(
    _list: MagicMock,
    mock_stop: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stop"])
    assert result.exit_code != 0
    mock_stop.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.stop_containers", return_value=["a"])
@patch(
    "cli.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_stop_with_yes(
    _list: MagicMock,
    mock_stop: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stop", "--yes"])
    assert result.exit_code == 0
    assert "stopped 1 container" in result.stdout
    mock_stop.assert_called_once_with(names=None)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.stop_containers", return_value=["web"])
@patch(
    "cli.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_stop_named_container(
    _list: MagicMock,
    mock_stop: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stop", "web", "--yes"])
    assert result.exit_code == 0
    mock_stop.assert_called_once_with(names=["web"])


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_containers",
    return_value=[
        ContainerRow("a", "/web", "running", 100, 200),
        ContainerRow("b", "/api", "exited", 50, 80),
    ],
)
def test_docker_containers_lists_all(_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "containers"])
    assert result.exit_code == 0
    assert "web" in result.stdout
    assert "api" in result.stdout
    _list.assert_called_once_with(all_containers=True, running_only=False)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.remove_containers")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_container_delete_requires_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "container-delete"])
    assert result.exit_code != 0
    mock_remove.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.remove_containers", return_value=["a", "b"])
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_container_delete_with_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "container-delete", "--yes"])
    assert result.exit_code == 0
    assert "deleted 2 container" in result.stdout
    mock_remove.assert_called_once_with(names=None)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.reset_docker")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_reset_requires_yes(
    _list: MagicMock,
    mock_reset: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "reset"])
    assert result.exit_code != 0
    mock_reset.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.reset_docker",
    return_value=ResetSummary(["a"], ["a", "b"], "reclaimed", "cache"),
)
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_reset_with_yes(
    _list: MagicMock,
    mock_reset: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "reset", "--yes"])
    assert result.exit_code == 0
    assert "build cache prune" in result.stdout
    mock_reset.assert_called_once_with(all_images=True)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.reset_docker",
    return_value=ResetSummary([], [], "dangling reclaimed", ""),
)
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_reset_dangling_only(
    _list: MagicMock,
    mock_reset: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "reset", "--yes", "--dangling-only"])
    assert result.exit_code == 0
    mock_reset.assert_called_once_with(all_images=False)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.remove_containers")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_containers_requires_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "containers"])
    assert result.exit_code != 0
    mock_remove.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_images")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_images_refuses(
    _list: MagicMock,
    mock_prune: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "images"])
    assert result.exit_code != 0
    mock_prune.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_build_cache")
@patch("cli.commands.docker.prune_images")
@patch("cli.commands.docker.remove_containers")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_all_refuses(
    _list: MagicMock,
    mock_remove: MagicMock,
    mock_prune: MagicMock,
    mock_cache: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "all"])
    assert result.exit_code != 0
    mock_remove.assert_not_called()
    mock_prune.assert_not_called()
    mock_cache.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.remove_containers", return_value=["a", "b"])
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_containers_with_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "containers", "--yes"])
    assert result.exit_code == 0
    assert "removed 2 container" in result.stdout
    mock_remove.assert_called_once_with()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_images")
@patch("cli.commands.docker.list_images", return_value=[])
def test_docker_image_delete_requires_yes(
    _images: MagicMock,
    mock_prune: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "image-delete"])
    assert result.exit_code != 0
    mock_prune.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_images", return_value="Total reclaimed: 1GB")
@patch("cli.commands.docker.list_containers", return_value=[])
@patch("cli.commands.docker.list_images", return_value=[])
def test_docker_image_delete_all(
    _list_images: MagicMock,
    _list_containers: MagicMock,
    mock_prune: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "image-delete", "--yes", "--all-images"])
    assert result.exit_code == 0
    assert "Total reclaimed" in result.stdout
    mock_prune.assert_called_once_with(all_unused=True)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_ps_empty(_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "ps"])
    assert result.exit_code == 0
    assert "no running containers" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_container_stats", return_value=[])
def test_docker_stats_empty(_stats: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "stats", "--by", "cpu"])
    assert result.exit_code == 0
    assert "no running containers" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_stats_storage_empty(_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "stats", "--by", "storage"])
    assert result.exit_code == 0
    assert "no running containers" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_container_stats",
    return_value=[ContainerStatsRow("a", "web", 1.0, 100, 1000, 10.0)],
)
@patch(
    "cli.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_stats_all_domains(
    _list: MagicMock,
    _stats: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stats", "--by", "all"])
    assert result.exit_code == 0
    assert "CPU" in result.stdout
    assert "memory" in result.stdout.lower()
    assert "storage" in result.stdout.lower()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_containers_empty(_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "containers"])
    assert result.exit_code == 0
    assert "no containers" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_images", return_value=[])
def test_docker_images_empty(_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "images"])
    assert result.exit_code == 0
    assert "no images" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.list_images", return_value=[])
@patch("cli.commands.docker.list_container_stats", return_value=[])
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_top_empty(
    _list: MagicMock,
    _stats: MagicMock,
    _images: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "top"])
    assert result.exit_code == 0
    assert "docker is empty" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.system_df", return_value="TYPE  TOTAL\nImages  1GB\n")
def test_docker_df(mock_df: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "df"])
    assert result.exit_code == 0
    assert "Images" in result.stdout
    mock_df.assert_called_once()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.stop_containers")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_stop_no_running(
    _list: MagicMock,
    mock_stop: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "stop", "--yes"])
    assert result.exit_code == 0
    assert "no running containers" in result.stdout
    mock_stop.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.remove_containers", return_value=["web"])
@patch(
    "cli.commands.docker.list_containers",
    return_value=[ContainerRow("abc", "/web", "exited", 100, 200)],
)
def test_docker_container_delete_named(
    _list: MagicMock,
    mock_remove: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "container-delete", "web", "--yes"])
    assert result.exit_code == 0
    assert "deleted 1 container" in result.stdout
    mock_remove.assert_called_once_with(names=["web"])


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_images", return_value="")
@patch("cli.commands.docker.list_containers", return_value=[])
@patch("cli.commands.docker.list_images", return_value=[])
def test_docker_image_delete_dangling(
    _images: MagicMock,
    _containers: MagicMock,
    mock_prune: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "image-delete", "--yes"])
    assert result.exit_code == 0
    assert "image prune" in result.stdout
    mock_prune.assert_called_once_with(all_unused=False)


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_build_cache", return_value="cache reclaimed")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_cache_with_yes(
    _list: MagicMock,
    mock_cache: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "cache", "--yes"])
    assert result.exit_code == 0
    assert "build cache prune" in result.stdout
    mock_cache.assert_called_once()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_build_cache", return_value="")
@patch("cli.commands.docker.prune_images", return_value="")
@patch("cli.commands.docker.remove_containers", return_value=["a"])
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_all_with_yes(
    _list: MagicMock,
    mock_remove: MagicMock,
    mock_prune: MagicMock,
    mock_cache: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "all", "--yes"])
    assert result.exit_code == 0
    assert "removed 1 container" in result.stdout
    assert "image prune" in result.stdout
    assert "build cache prune" in result.stdout
    mock_remove.assert_called_once()
    mock_prune.assert_called_once_with(all_unused=False)
    mock_cache.assert_called_once()


@patch("cli.commands.docker.docker_available", return_value=True)
def test_docker_clean_invalid_target(_avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "clean", "bogus"])
    assert result.exit_code != 0


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_container_stats",
    return_value=[ContainerStatsRow("a", "web", 3.0, 200, 2000, 5.0)],
)
def test_docker_stats_memory(_stats: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "stats", "--by", "memory"])
    assert result.exit_code == 0
    assert "web" in result.stdout


@patch("cli.commands.docker.docker_available", return_value=True)
@patch("cli.commands.docker.prune_build_cache")
@patch("cli.commands.docker.list_containers", return_value=[])
def test_docker_clean_cache_refuses(
    _list: MagicMock,
    mock_cache: MagicMock,
    _avail: MagicMock,
) -> None:
    result = runner.invoke(app, ["docker", "clean", "cache"])
    assert result.exit_code != 0
    mock_cache.assert_not_called()


@patch("cli.commands.docker.docker_available", return_value=True)
@patch(
    "cli.commands.docker.list_containers",
    return_value=[ContainerRow("a", "/web", "running", 100, 200)],
)
def test_docker_containers_running_only(_list: MagicMock, _avail: MagicMock) -> None:
    result = runner.invoke(app, ["docker", "containers", "--running"])
    assert result.exit_code == 0
    assert "web" in result.stdout
    _list.assert_called_once_with(all_containers=False, running_only=True)
