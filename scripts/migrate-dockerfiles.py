#!/usr/bin/env python3
"""Copy hub docker/ images into each app repo as Dockerfile (or docker/ exceptions)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1]
GITHUB = PIPELINES.parent.parent
DOCKER = PIPELINES / "docker"

# config slug -> (source under docker/, dest relative to repo root)
APP_IMAGES: dict[str, tuple[str, str]] = {
    "animated-games": ("animated-games.dockerfile", "Dockerfile"),
    "chrome-extensions": ("chrome-extensions.dockerfile", "Dockerfile"),
    "database": ("database.dockerfile", "Dockerfile"),
    "gardusig": ("gardusig.dockerfile", "Dockerfile"),
    "static-puzzles": ("static-puzzles.dockerfile", "Dockerfile"),
    "github-pipelines": ("github-pipelines.dockerfile", "Dockerfile"),
    "python-cli": ("python-cli.dockerfile", "Dockerfile"),
    "wiki": ("wiki.dockerfile", "Dockerfile"),
    "cpp": ("cpp/cpp.dockerfile", "Dockerfile"),
    "go": ("go/go.dockerfile", "Dockerfile"),
    "tex": ("tex/tex.dockerfile", "docker/Dockerfile"),
}

LANGUAGE_REPOS = (
    "assembly",
    "c",
    "csharp",
    "clojure",
    "css",
    "dart",
    "elixir",
    "fsharp",
    "haskell",
    "html",
    "java",
    "javascript",
    "julia",
    "kotlin",
    "lua",
    "perl",
    "prolog",
    "php",
    "powershell",
    "python",
    "r",
    "ruby",
    "rust",
    "scala",
    "shell",
    "sql",
    "swift",
    "typescript",
    "visual-basic",
    "protobuf",
    "graphql",
    "terraform",
    "dockerfile",
    "docs",
    "groovy",
    "erlang",
    "objective-c",
    "nim",
    "zig",
)

CONFIG_TO_REPO: dict[str, tuple[str, str]] = {
    "animated-games": ("public", "animated-games"),
    "assembly": ("public", "assembly"),
    "c": ("public", "c"),
    "chrome-extensions": ("public", "chrome-extensions"),
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

WORKDIR_FIXES = (
    ("/workspace/github-pipelines", "/workspace"),
    ("/workspace/python-cli", "/workspace"),
)


def _transform(content: str) -> str:
    for old, new in WORKDIR_FIXES:
        content = content.replace(old, new)
    content = re.sub(
        r"cli structure check /workspace/github-pipelines",
        "cli structure check /workspace",
        content,
    )
    content = re.sub(
        r"cli lint repo /workspace/github-pipelines",
        "cli lint repo /workspace",
        content,
    )
    return content


def _write_image(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_transform(source.read_text(encoding="utf-8")), encoding="utf-8")


def _patch_pull_request_config(config_path: Path, *, dest: str) -> None:
    if not config_path.is_file():
        return
    lines: list[str] = []
    skip = {"dockerfile", "dockerignore"}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        key = line.split(":", 1)[0].strip()
        if key in skip:
            continue
        lines.append(line)
    text = "\n".join(lines).rstrip() + "\n"
    if dest.startswith("docker/"):
        text = text.replace("jobs:\n", f"dockerfile: {dest}\njobs:\n", 1)
    config_path.write_text(text, encoding="utf-8")


def main() -> None:
    migrated = 0
    for slug, (visibility, repo_name) in CONFIG_TO_REPO.items():
        if slug in LANGUAGE_REPOS:
            source_rel, dest_rel = "language-repo.dockerfile", "Dockerfile"
        elif slug == "cpp-compile":
            source_rel, dest_rel = APP_IMAGES["cpp"]
        elif slug == "go-test":
            source_rel, dest_rel = APP_IMAGES["go"]
        elif slug in APP_IMAGES:
            source_rel, dest_rel = APP_IMAGES[slug]
        else:
            continue

        repo_root = GITHUB / visibility / repo_name
        if not repo_root.is_dir():
            print(f"skip missing repo: {visibility}/{repo_name}")
            continue

        source = DOCKER / source_rel
        if not source.is_file():
            print(f"skip missing source: {source_rel}")
            continue

        dest = repo_root / dest_rel
        _write_image(source, dest)
        if slug == "python-cli":
            ignore_src = DOCKER / "python-cli.dockerignore"
            if ignore_src.is_file():
                ignore_text = ignore_src.read_text(encoding="utf-8").replace(".github/\n", "")
                (repo_root / ".dockerignore").write_text(ignore_text, encoding="utf-8")

        if slug == "wiki":
            mermaid_src = DOCKER / "wiki" / "mermaid.dockerfile"
            if mermaid_src.is_file():
                _write_image(mermaid_src, repo_root / "docker" / "mermaid.Dockerfile")

        _patch_pull_request_config(repo_root / ".github" / "pull-request.yaml", dest=dest_rel)
        print(f"wrote {dest.relative_to(GITHUB)}")
        migrated += 1

    # Hub keeps operator + cli-base only under docker/
    hub_dockerfile = PIPELINES / "Dockerfile"
    _write_image(DOCKER / "github-pipelines.dockerfile", hub_dockerfile)
    _patch_pull_request_config(PIPELINES / ".github" / "pull-request.yaml", dest="Dockerfile")
    print(f"wrote {hub_dockerfile.relative_to(GITHUB)}")

    remove_paths = [
        DOCKER / name
        for name in (
            "animated-games.dockerfile",
            "chrome-extensions.dockerfile",
            "database.dockerfile",
            "gardusig.dockerfile",
            "static-puzzles.dockerfile",
            "github-pipelines.dockerfile",
            "python-cli.dockerfile",
            "python-cli.dockerignore",
            "wiki.dockerfile",
            "language-repo.dockerfile",
            "markdown.dockerfile",
            "animated-games.dockerfile",
        )
    ]
    remove_paths.extend(
        [
            DOCKER / "cpp",
            DOCKER / "go",
            DOCKER / "tex",
            DOCKER / "wiki",
            DOCKER / "interviewing",
        ]
    )
    for path in remove_paths:
        if path.is_dir():
            shutil.rmtree(path)
            print(f"removed dir {path.relative_to(PIPELINES)}")
        elif path.is_file():
            path.unlink()
            print(f"removed {path.relative_to(PIPELINES)}")

    print(f"migrated {migrated} app repos")


if __name__ == "__main__":
    main()
