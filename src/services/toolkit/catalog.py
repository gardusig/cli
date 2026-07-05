from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    group: str
    subject: str
    suite: str | None
    description: str
    script: str
    markers: tuple[str, ...] = ()
    requires_bins: tuple[str, ...] = ()
    requires_any_bins: tuple[str, ...] = ()
    language: str | None = None


COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("lint", "repo", None, "Run every lint for languages present in this repo.", "scripts/toolkit/lint-repo.sh"),
    CommandSpec("lint", "markdown", None, "Lint Markdown and Mermaid fences.", "scripts/markdown/lint.sh", language="markdown"),
    CommandSpec("lint", "python", None, "Syntax-check Python sources.", "scripts/python/lint.sh", ("pyproject.toml", "setup.py", "requirements.txt", "*.py"), ("python3",), language="python"),
    CommandSpec("lint", "typescript", None, "Run TypeScript lint scripts.", "scripts/typescript/lint.sh", ("package.json",), ("node", "npm"), language="typescript"),
    CommandSpec("lint", "cpp", None, "Run C++ formatting checks.", "scripts/cpp/lint.sh", ("CMakeLists.txt", "*.cpp"), ("clang-format",), language="cpp"),
    CommandSpec("lint", "shell", None, "Syntax-check shell scripts.", "scripts/shell/lint.sh", ("*.sh",), ("bash",), language="shell"),
    CommandSpec("lint", "java", None, "Run Java lint/checkstyle.", "scripts/java/lint.sh", ("pom.xml", "build.gradle", "build.gradle.kts"), ("java", "javac"), ("mvn", "gradle"), "java"),
    CommandSpec("test", "python", "unit", "Run Python unit tests.", "scripts/python/test-unit.sh", ("pyproject.toml", "setup.py"), ("python3",), language="python"),
    CommandSpec("test", "python", "integration", "Run Python integration tests.", "scripts/python/test-integration.sh", ("pyproject.toml", "setup.py"), ("python3",), language="python"),
    CommandSpec("test", "python", "command-surface", "Run Python command surface checks.", "scripts/python/test-command-surface.sh", ("pyproject.toml", "setup.py"), ("python3",), language="python"),
    CommandSpec("test", "typescript", "unit", "Run TypeScript tests.", "scripts/typescript/test.sh", ("package.json",), ("node", "npm"), language="typescript"),
    CommandSpec("test", "typescript", "build", "Run TypeScript build.", "scripts/typescript/build.sh", ("package.json",), ("node", "npm"), language="typescript"),
    CommandSpec("test", "cpp", "compile", "Compile C++ sources.", "scripts/cpp/compile.sh", ("*.cpp",), ("g++",), language="cpp"),
    CommandSpec("test", "cpp", "smoke", "Run C++ smoke tests.", "scripts/cpp/smoke.sh", ("*.cpp",), ("g++",), language="cpp"),
    CommandSpec("test", "java", "unit", "Run Java unit tests.", "scripts/java/test-unit.sh", ("pom.xml", "build.gradle", "build.gradle.kts"), ("java", "javac"), ("mvn", "gradle"), "java"),
    CommandSpec("structure", "check", None, "Check repository structure policy.", "scripts/structure/check.sh"),
    CommandSpec("validate", "vault", None, "Validate vault/database data.", "scripts/validate/vault.sh"),
    CommandSpec("validate", "tasks", None, "Validate task pair data.", "scripts/validate/tasks.sh"),
    CommandSpec("languages", "list", None, "List supported toolkit languages.", "scripts/toolkit/languages-list.sh"),
    CommandSpec("languages", "show", None, "Show one language's commands and prerequisites.", "scripts/toolkit/languages-show.sh"),
)

_COMMAND_INDEX = {(spec.group, spec.subject, spec.suite): spec for spec in COMMANDS}

REPO_LANGUAGE_PROFILES: dict[str, tuple[str, ...]] = {
    "animated-games": ("markdown", "typescript"),
    "chrome-extensions": ("markdown", "typescript"),
    "computer-science": ("markdown", "cpp"),
    "database": ("markdown",),
    "gardusig": ("markdown",),
    "github-pipelines": ("markdown", "python", "shell"),
    "python-cli": ("markdown", "python", "shell"),
    "static-puzzles": ("markdown", "typescript"),
    "wiki": ("markdown",),
}


def command_spec(group: str, subject: str, suite: str | None = None) -> CommandSpec:
    try:
        return _COMMAND_INDEX[(group, subject, suite)]
    except KeyError as exc:
        suffix = f" {suite}" if suite else ""
        raise KeyError(f"unknown toolkit command: {group} {subject}{suffix}") from exc


def languages() -> tuple[str, ...]:
    return tuple(sorted({spec.language for spec in COMMANDS if spec.language}))


def lint_languages() -> tuple[str, ...]:
    return tuple(spec.subject for spec in COMMANDS if spec.group == "lint" and spec.subject != "repo")


def specs_for_language(language: str) -> tuple[CommandSpec, ...]:
    return tuple(spec for spec in COMMANDS if spec.language == language)

