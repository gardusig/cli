from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    group: str
    subject: str
    suite: str | None
    description: str
    handler: str
    markers: tuple[str, ...] = ()
    requires_bins: tuple[str, ...] = ()
    requires_any_bins: tuple[str, ...] = ()
    language: str | None = None


COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("lint", "repo", None, "Run every lint for languages present in this repo.", "lint_repo"),
    CommandSpec("lint", "markdown", None, "Lint Markdown and Mermaid fences.", "lint_markdown", language="markdown"),
    CommandSpec("lint", "python", None, "Syntax-check Python sources.", "lint_python", ("pyproject.toml", "setup.py", "requirements.txt", "*.py"), ("python3",), language="python"),
    CommandSpec("lint", "typescript", None, "Run TypeScript lint scripts.", "lint_typescript", ("package.json",), ("node", "npm"), language="typescript"),
    CommandSpec("lint", "cpp", None, "Run C++ formatting checks.", "lint_cpp", ("CMakeLists.txt", "*.cpp"), ("clang-format",), language="cpp"),
    CommandSpec("lint", "shell", None, "Syntax-check shell scripts.", "lint_shell", ("*.sh",), ("bash",), language="shell"),
    CommandSpec("lint", "java", None, "Run Java lint/checkstyle.", "lint_java", ("pom.xml", "build.gradle", "build.gradle.kts"), ("java", "javac"), ("mvn", "gradle"), "java"),
    CommandSpec("test", "python", "unit", "Run Python unit tests.", "test_python_unit", ("pyproject.toml", "setup.py"), ("python3",), language="python"),
    CommandSpec("test", "python", "integration", "Run Python integration tests.", "test_python_integration", ("pyproject.toml", "setup.py"), ("python3",), language="python"),
    CommandSpec("test", "python", "command-surface", "Run Python command surface checks.", "test_python_command_surface", ("pyproject.toml", "setup.py"), ("python3",), language="python"),
    CommandSpec("test", "typescript", "unit", "Run TypeScript tests.", "test_typescript_unit", ("package.json",), ("node", "npm"), language="typescript"),
    CommandSpec("test", "typescript", "build", "Run TypeScript build.", "test_typescript_build", ("package.json",), ("node", "npm"), language="typescript"),
    CommandSpec("test", "cpp", "compile", "Compile C++ sources.", "test_cpp_compile", ("*.cpp",), ("g++",), language="cpp"),
    CommandSpec("test", "cpp", "smoke", "Run C++ smoke tests.", "test_cpp_smoke", ("*.cpp",), ("g++",), language="cpp"),
    CommandSpec("test", "java", "unit", "Run Java unit tests.", "test_java_unit", ("pom.xml", "build.gradle", "build.gradle.kts"), ("java", "javac"), ("mvn", "gradle"), "java"),
    CommandSpec("structure", "check", None, "Check repository structure policy.", "structure_check"),
    CommandSpec("validate", "vault", None, "Validate vault/database data.", "validate_vault"),
    CommandSpec("validate", "tasks", None, "Validate task pair data.", "validate_tasks"),
    CommandSpec("languages", "list", None, "List supported toolkit languages.", "languages_list"),
    CommandSpec("languages", "show", None, "Show one language's commands and prerequisites.", "languages_show"),
)

_COMMAND_INDEX = {(spec.group, spec.subject, spec.suite): spec for spec in COMMANDS}

REPO_LANGUAGE_PROFILES: dict[str, tuple[str, ...]] = {
    "animated-games": ("markdown", "typescript"),
    "chrome-extensions": ("markdown", "typescript"),
    "interviewing": ("markdown", "cpp"),
    "code": ("go",),
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

