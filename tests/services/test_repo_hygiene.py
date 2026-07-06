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
    (root / "config.yaml").write_text("bad: true\n", encoding="utf-8")

    policy = HygienePolicy.from_mapping(
        {
            "allowed_extensions": [".dockerfile", ".md", ".yaml", ".yml"],
            "allowed_filenames": [".gitignore", "README.md"],
            "allowed_root_dirs": [".github", "docker", "docs"],
            "allowed_root_files": [".gitignore", "README.md"],
            "max_depth": 3,
        }
    )

    errors = check_repo_hygiene(root, require_structure=True, policy=policy)

    assert "unexpected root directory: scripts/" in errors
    assert "unexpected root file: config.yaml" in errors


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
