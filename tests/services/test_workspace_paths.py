from __future__ import annotations

from pathlib import Path

from src.services.workspace_paths import check_workspace_paths, load_required_paths


def test_load_required_paths_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    manifest = tmp_path / "required-paths.txt"
    manifest.write_text(
        "\n".join(
            [
                "# workspace paths",
                "",
                "public/",
                "public/index/README.md # inline comment",
                " private/ ",
            ]
        ),
        encoding="utf-8",
    )

    paths = load_required_paths(manifest)

    assert [path.path for path in paths] == ["public", "public/index/README.md", "private"]
    assert [path.line_number for path in paths] == [3, 4, 5]


def test_check_workspace_paths_reports_missing_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "github"
    (workspace / "public" / "index").mkdir(parents=True)
    (workspace / "public" / "index" / "README.md").write_text("# index\n", encoding="utf-8")
    manifest = tmp_path / "required-paths.txt"
    manifest.write_text("public/index/README.md\nprivate\n", encoding="utf-8")

    result = check_workspace_paths(manifest, workspace_root=workspace)

    assert result.checked == 2
    assert result.skipped == 0
    assert [missing.path for missing in result.missing] == ["private"]


def test_check_workspace_paths_maps_base_to_repo_root(tmp_path: Path) -> None:
    repo = tmp_path / "index"
    repo.mkdir()
    (repo / "README.md").write_text("# index\n", encoding="utf-8")
    manifest = tmp_path / "required-paths.txt"
    manifest.write_text(
        "\n".join(
            [
                "private",
                "public/gardusig",
                "public/index",
                "public/index/README.md",
                "public/index/missing.md",
            ]
        ),
        encoding="utf-8",
    )

    result = check_workspace_paths(manifest, workspace_root=tmp_path, base="public/index", repo_root=repo)

    assert result.checked == 3
    assert result.skipped == 2
    assert [missing.path for missing in result.missing] == ["public/index/missing.md"]
