#!/usr/bin/env python3
"""Move pull-request pipeline configs from gardusig/cli into each app repo."""

from __future__ import annotations

from pathlib import Path

import yaml

PIPELINES = Path(__file__).resolve().parents[1]


def _github_root() -> Path:
    path = Path(__file__).resolve()
    for _ in range(8):
        if (path / "public" / "python-cli").is_dir():
            return path
        path = path.parent
    raise RuntimeError("could not find github checkout root (expected public/python-cli)")


GITHUB = _github_root()
CONFIG_DIR = PIPELINES / ".github" / "workflows" / "pull-request"
ROUTER = "gardusig/cli/.github/workflows/lib/pull-request-router.yml@main"

CONFIG_TO_REPO: dict[str, tuple[str, str]] = {
    "animated-games": ("public", "animated-games"),
    "assembly": ("public", "assembly"),
    "c": ("public", "c"),
    "chrome-extensions": ("public", "chrome-extensions"),
    "code": ("public", "code"),
    "cpp-compile": ("public", "cpp"),
    "csharp": ("public", "csharp"),
    "clojure": ("public", "clojure"),
    "css": ("public", "css"),
    "dart": ("public", "dart"),
    "database": ("private", "database"),
    "elixir": ("public", "elixir"),
    "fsharp": ("public", "fsharp"),
    "gardusig": ("public", "gardusig"),
    "github-pipelines": ("public", "github-pipelines"),
    "go-test": ("public", "go"),
    "haskell": ("public", "haskell"),
    "html": ("public", "html"),
    "java": ("public", "java"),
    "javascript": ("public", "javascript"),
    "julia": ("public", "julia"),
    "kotlin": ("public", "kotlin"),
    "lua": ("public", "lua"),
    "perl": ("public", "perl"),
    "prolog": ("public", "prolog"),
    "php": ("public", "php"),
    "powershell": ("public", "powershell"),
    "python-cli": ("public", "python-cli"),
    "python": ("public", "python"),
    "r": ("public", "r"),
    "ruby": ("public", "ruby"),
    "rust": ("public", "rust"),
    "scala": ("public", "scala"),
    "shell": ("public", "shell"),
    "sql": ("public", "sql"),
    "static-puzzles": ("public", "static-puzzles"),
    "swift": ("public", "swift"),
    "tex": ("private", "tex"),
    "typescript": ("public", "typescript"),
    "visual-basic": ("public", "visual-basic"),
    "wiki": ("private", "wiki"),
    "protobuf": ("public", "protobuf"),
    "graphql": ("public", "graphql"),
    "terraform": ("public", "terraform"),
    "dockerfile": ("public", "dockerfile"),
    "docs": ("public", "docs"),
    "groovy": ("public", "groovy"),
    "erlang": ("public", "erlang"),
    "objective-c": ("public", "objective-c"),
    "nim": ("public", "nim"),
    "ansible": ("public", "ansible"),
    "avro": ("public", "avro"),
    "bazel": ("public", "bazel"),
    "bicep": ("public", "bicep"),
    "cuda": ("public", "cuda"),
    "cue": ("public", "cue"),
    "hcl": ("public", "hcl"),
    "nix": ("public", "nix"),
    "ocaml": ("public", "ocaml"),
    "raml": ("public", "raml"),
    "rego": ("public", "rego"),
    "scss": ("public", "scss"),
    "solidity": ("public", "solidity"),
    "thrift": ("public", "thrift"),
    "toml": ("public", "toml"),
    "vue": ("public", "vue"),
    "wasm": ("public", "wasm"),
    "ada": ("public", "ada"),
    "crystal": ("public", "crystal"),
    "fortran": ("public", "fortran"),
    "lisp": ("public", "lisp"),
    "scheme": ("public", "scheme"),
    "zig": ("public", "zig"),
    "json": ("public", "json"),
    "kafka": ("public", "kafka"),
    "kubernetes": ("public", "kubernetes"),
}

SKIP_CONFIGS = {"python-cli", "index"}
PAGES_REPOS = {"tex"}
PYPI_CONFIGS = {"python-cli"}

CALLER_SLUG: dict[str, str] = {
    "python-cli": "cli",
    "github-pipelines": "yaml",
}

CALLER_REPOSITORY: dict[str, str] = {
    "python-cli": "gardusig/cli",
    "github-pipelines": "gardusig/cli",
}

WIKI_WORKFLOW = f"""\
name: Pull request

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

concurrency:
  group: pr-${{{{ github.event.pull_request.number }}}}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  markdown-only:
    name: Markdown-only guard
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Reject non-markdown tracked files
        run: |
          set -euo pipefail
          bad=$(
            git ls-files \\
              | grep -Ev '(^\\.gitignore$|^\\.gitmodules$|^repos/Makefile$|\\.md$|\\.github/workflows/.*\\.ya?ml$|^repos/(public|private)/[^/]+$|^\\.github/pull-request\\.ya?ml$)' \\
              || true
          )
          if [ -n "$bad" ]; then
            echo "::error::Wiki must stay markdown-only. Remove or move these files:"
            echo "$bad"
            exit 1
          fi

  pipeline:
    needs: markdown-only
    uses: {ROUTER}
    with:
      repo_slug: wiki
      repository: gardusig/wiki
      ref: ${{{{ github.event.pull_request.head.ref }}}}
      sha: ${{{{ github.event.pull_request.head.sha }}}}
      pr_number: ${{{{ github.event.pull_request.number }}}}
    secrets:
      CENTRAL_PIPELINE_PAT: ${{{{ secrets.CENTRAL_PIPELINE_PAT }}}}
"""


def repo_slug_from_config_name(name: str) -> str:
    if name in CALLER_SLUG:
        return CALLER_SLUG[name]
    if name in {"cpp-compile", "go-test"}:
        return name.split("-", 1)[0]
    return name


def caller_repository(config_name: str, slug: str) -> str:
    if config_name in CALLER_REPOSITORY:
        return CALLER_REPOSITORY[config_name]
    return f"gardusig/{slug}"


def ensure_allowed_path(data: dict) -> dict:
    for job in data.get("jobs") or []:
        if not isinstance(job, dict) or job.get("id") != "repo-hygiene":
            continue
        policy = job.setdefault("hygiene_policy", {})
        paths = set(policy.get("allowed_paths") or [])
        paths.add(".github/pull-request.yaml")
        policy["allowed_paths"] = sorted(paths)
        extensions = set(policy.get("allowed_extensions") or [])
        if ".yaml" not in extensions and ".yml" in extensions:
            extensions.add(".yaml")
            policy["allowed_extensions"] = sorted(extensions)
    return data


def sanitize_config(data: dict, config_name: str) -> dict:
    data.pop("dockerfile", None)
    data.pop("dockerignore", None)
    if config_name == "python-cli":
        data["repo"] = "gardusig/cli"
    elif config_name == "github-pipelines":
        data["repo"] = "gardusig/cli"
    return data


def merge_wiki_configs() -> dict:
    wiki = yaml.safe_load((CONFIG_DIR / "wiki.yaml").read_text(encoding="utf-8"))
    mermaid = yaml.safe_load((CONFIG_DIR / "wiki-mermaid.yaml").read_text(encoding="utf-8"))
    wiki_jobs = {job["id"]: job for job in wiki.get("jobs") or [] if isinstance(job, dict)}
    for job in mermaid.get("jobs") or []:
        if not isinstance(job, dict):
            continue
        if job.get("id") == "validate" and "validate" not in wiki_jobs:
            validate = dict(job)
            validate["needs"] = "repo-hygiene"
            wiki["jobs"].append(validate)
    return wiki


def caller_workflow(config_name: str, slug: str, *, pages: bool = False, tex_paths: bool = False) -> str:
    repository = caller_repository(config_name, slug)
    lines = [
        "name: Pull request",
        "",
        "on:",
        "  pull_request:",
        "    branches: [main]",
        "    types: [opened, synchronize, reopened]",
    ]
    if tex_paths:
        lines.extend(
            [
                "    paths:",
                "      - 'lib/**'",
                "      - 'versions/**'",
                "      - 'Makefile'",
                "      - '**/*.md'",
                "      - '.github/workflows/pull-request.yml'",
                "      - '.github/pull-request.yaml'",
            ]
        )
    lines.extend(
        [
            "",
            "concurrency:",
            "  group: pr-${{ github.event.pull_request.number }}",
            "  cancel-in-progress: true",
            "",
            "permissions:",
            "  contents: read",
            "",
            "jobs:",
            "  pipeline:",
        ]
    )
    if pages or config_name in PYPI_CONFIGS:
        lines.append("    permissions:")
        lines.append("      contents: read")
    if pages:
        lines.extend(["      pages: write", "      id-token: write"])
    if config_name in PYPI_CONFIGS:
        if not pages:
            lines.append("      pages: write")
            lines.append("      id-token: write")
    lines.extend(
        [
            f"    uses: {ROUTER}",
            "    with:",
            f"      repo_slug: {slug}",
            f"      repository: {repository}",
            "      ref: ${{ github.event.pull_request.head.ref }}",
            "      sha: ${{ github.event.pull_request.head.sha }}",
            "      pr_number: ${{ github.event.pull_request.number }}",
            "    secrets:",
            "      CENTRAL_PIPELINE_PAT: ${{ secrets.CENTRAL_PIPELINE_PAT }}",
        ]
    )
    if config_name in PYPI_CONFIGS:
        lines.extend(
            [
                "      TESTPYPI_API_TOKEN: ${{ secrets.TESTPYPI_API_TOKEN }}",
                "      PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    merged_wiki = merge_wiki_configs()
    for config_name, (visibility, repo_name) in CONFIG_TO_REPO.items():
        if config_name in SKIP_CONFIGS:
            print(f"skip manual config: {config_name}")
            continue
        if config_name == "wiki-mermaid":
            continue
        repo_root = GITHUB / visibility / repo_name
        if not repo_root.is_dir():
            print(f"skip missing repo: {visibility}/{repo_name}")
            continue

        if config_name == "wiki":
            data = merged_wiki
        else:
            source = CONFIG_DIR / f"{config_name}.yaml"
            if not source.is_file():
                print(f"skip missing config: {config_name}")
                continue
            data = yaml.safe_load(source.read_text(encoding="utf-8"))

        data = sanitize_config(data, config_name)
        data = ensure_allowed_path(data)
        config_path = repo_root / ".github" / "pull-request.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

        slug = repo_slug_from_config_name(config_name)
        workflow_path = repo_root / ".github" / "workflows" / "pull-request.yml"
        if config_name == "wiki":
            workflow_path.write_text(WIKI_WORKFLOW, encoding="utf-8")
        else:
            workflow_path.parent.mkdir(parents=True, exist_ok=True)
            workflow_path.write_text(
                caller_workflow(
                    config_name,
                    slug,
                    pages=slug in PAGES_REPOS,
                    tex_paths=slug == "tex",
                ),
                encoding="utf-8",
            )
        print(f"migrated {config_name} -> {visibility}/{repo_name}")


if __name__ == "__main__":
    main()
