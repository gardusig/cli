from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.services.repo_hygiene import HygienePolicy, check_repo_hygiene, load_hygiene_policy


runner = CliRunner()


def _standard_repo(root: Path) -> None:
    (root / "src").mkdir()
    (root / "docs").mkdir()
    (root / "tests").mkdir()
    (root / "README.md").write_text("# Repo\n", encoding="utf-8")


def test_hygiene_policy_allows_extensions_and_filenames(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".md", "py"],
            "allowed_filenames": ["LICENSE"],
        }
    )

    assert check_repo_hygiene(tmp_path, require_layout=True, policy=policy) == []


def test_hygiene_policy_rejects_disallowed_extension(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "src" / "main.rs").write_text("fn main() {}\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping({"allowed_extensions": [".md", ".py"]})

    errors = check_repo_hygiene(tmp_path, require_layout=True, policy=policy)

    assert "file type is not allowed by hygiene policy: src/main.rs" in errors


def test_shell_scripts_outside_python_cli_point_to_cli_repo(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "deploy.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping({"allowed_extensions": [".md", ".sh"]})

    errors = check_repo_hygiene(tmp_path, require_layout=True, policy=policy)

    assert (
        "shell script belongs in gardusig/python-cli: src/deploy.sh "
        "(move this script to the CLI repo and expose it through a cli command)"
    ) in errors


def test_python_cli_policy_rejects_shell_scripts(tmp_path: Path) -> None:
    root = tmp_path / "python-cli"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "tests").mkdir()
    (root / "README.md").write_text("# CLI\n", encoding="utf-8")
    (root / "src" / "tool.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".md", ".sh"],
            "forbidden_extensions": [".sh"],
            "forbidden_messages": {
                ".sh": "Shell scripts belong in gardusig/python-cli. Move this script there and expose it through a cli command."
            },
        }
    )

    errors = check_repo_hygiene(root, require_layout=True, policy=policy)

    assert (
        "Shell scripts belong in gardusig/python-cli. Move this script there and "
        "expose it through a cli command.: src/tool.sh"
    ) in errors


def test_app_repo_direct_cli_reference_belongs_in_pipelines(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "docs" / "run.md").write_text("Run `cli lint repo` locally.\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {"allowed_extensions": [".md"], "forbid_direct_cli_references": True}
    )

    errors = check_repo_hygiene(tmp_path, require_layout=True, policy=policy)

    assert "direct cli reference belongs in github-pipelines: docs/run.md" in errors


def test_database_style_policy_rejects_markdown(tmp_path: Path) -> None:
    (tmp_path / "tasks" / "body").mkdir(parents=True)
    (tmp_path / "tasks" / "body" / "note.md").write_text("## Steps\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_root_dirs": ["tasks"],
            "allowed_root_files": [],
            "allowed_extensions": [".yaml", ".yml", ".json", ".pdf"],
        }
    )

    errors = check_repo_hygiene(tmp_path, require_structure=True, policy=policy)

    assert "file type is not allowed by hygiene policy: tasks/body/note.md" in errors


def test_forbidden_globs_override_allowlist(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    secret = tmp_path / "docs" / "private.md"
    secret.write_text("secret\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".md"],
            "forbidden_globs": ["docs/private.*"],
            "forbidden_messages": {"docs/private.*": "private docs belong in wiki"},
        }
    )

    errors = check_repo_hygiene(tmp_path, require_layout=True, policy=policy)

    assert "private docs belong in wiki: docs/private.md" in errors


def test_hygiene_policy_ignores_generated_prefixes(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "snapshot.rs").write_text("fn main() {}\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".md", ".py"],
            "ignored_prefixes": ["generated"],
        }
    )

    assert check_repo_hygiene(tmp_path, require_layout=True, policy=policy) == []


def test_load_hygiene_policy_from_yaml(tmp_path: Path) -> None:
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(
        "allowed_extensions:\n  - md\nallowed_filenames:\n  - LICENSE\n",
        encoding="utf-8",
    )

    policy = load_hygiene_policy(policy_file)

    assert ".md" in policy.allowed_extensions
    assert "LICENSE" in policy.allowed_filenames


def test_hygiene_policy_rejects_depth_violation(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    deep = tmp_path / "src" / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "note.md").write_text("deep\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".md", ".py"],
            "max_depth": 3,
        }
    )

    errors = check_repo_hygiene(tmp_path, require_structure=True, policy=policy)

    assert "directory exceeds max depth 3: src/a/b/c/" in errors


def test_hygiene_policy_rejects_unexpected_root_dir(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "unexpected").mkdir()

    policy = HygienePolicy.from_mapping({"allowed_extensions": [".md", ".py"]})

    errors = check_repo_hygiene(tmp_path, require_structure=True, policy=policy)

    assert "unexpected root directory: unexpected/" in errors


def test_hygiene_policy_rejects_unexpected_root_file_when_allowlist_declared(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".md", ".toml"],
            "allowed_root_dirs": ["src", "docs", "tests"],
            "allowed_root_files": ["README.md"],
        }
    )

    errors = check_repo_hygiene(tmp_path, require_structure=True, policy=policy)

    assert "unexpected root file: pyproject.toml" in errors


def test_github_pipelines_policy_allows_only_workflows_docker_docs_and_known_root_files(
    tmp_path: Path,
) -> None:
    root = tmp_path / "github-pipelines"
    (root / ".github" / "workflows" / "pull-request").mkdir(parents=True)
    (root / "docker").mkdir()
    (root / "docs").mkdir()
    (root / "README.md").write_text("# Pipelines\n", encoding="utf-8")
    (root / ".gitignore").write_text(".env\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "docs" / "build.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (root / "config.yaml").write_text("bad: true\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".dockerfile", ".md", ".yaml", ".yml"],
            "forbidden_extensions": [".sh"],
            "forbidden_messages": {
                ".sh": "Shell scripts belong in gardusig/python-cli. Move this script there and expose it through a cli command."
            },
            "allowed_filenames": [".gitignore", "README.md"],
            "allowed_root_dirs": [".github", "docker", "docs"],
            "allowed_root_files": [".gitignore", "README.md"],
            "max_depth": 3,
        }
    )

    errors = check_repo_hygiene(root, require_structure=True, policy=policy)

    assert "unexpected root directory: scripts/" in errors
    assert "unexpected root file: config.yaml" in errors
    assert (
        "Shell scripts belong in gardusig/python-cli. Move this script there and "
        "expose it through a cli command.: docs/build.sh"
    ) in errors


def test_structure_cli_accepts_policy_file(tmp_path: Path) -> None:
    _standard_repo(tmp_path)
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text("allowed_extensions:\n  - .md\n  - .py\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["structure", "check", str(tmp_path), "--require-layout", "--policy-file", str(policy_file)],
    )

    assert result.exit_code == 0
    assert "structure ok" in result.stdout
