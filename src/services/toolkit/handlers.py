from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from src.services.notion_pairs import load_pairs, pair_file_warning, scan_task_root
from src.services.repo_hygiene import check_repo_hygiene, load_hygiene_policy, policy_with_ignored_paths
from src.services.toolkit.catalog import CommandSpec, languages, specs_for_language
from src.services.toolkit.detect import repo_languages

IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}


def run_handler(spec: CommandSpec, workspace: Path, extra_env: dict[str, str] | None = None) -> int:
    handlers = {
        "lint_repo": _lint_repo,
        "lint_markdown": _lint_markdown,
        "lint_python": _lint_python,
        "lint_typescript": _lint_typescript,
        "lint_cpp": _lint_cpp,
        "lint_shell": _lint_shell,
        "lint_java": _lint_java,
        "test_python_unit": _test_python_unit,
        "test_python_integration": _test_python_integration,
        "test_python_command_surface": _test_python_command_surface,
        "test_typescript_unit": _test_typescript_unit,
        "test_typescript_build": _test_typescript_build,
        "test_cpp_compile": _test_cpp_compile,
        "test_cpp_smoke": _test_cpp_smoke,
        "test_java_unit": _test_java_unit,
        "structure_check": _structure_check,
        "validate_tasks": _validate_tasks,
        "languages_list": _languages_list,
        "languages_show": _languages_show,
    }
    try:
        handler = handlers[spec.handler]
    except KeyError as exc:
        raise KeyError(f"unknown toolkit handler: {spec.handler}") from exc
    return handler(spec, workspace, extra_env or {})


def _run(cmd: list[str], workspace: Path) -> int:
    return subprocess.run(cmd, cwd=workspace, check=False).returncode


def _run_checked(cmd: list[str], workspace: Path) -> None:
    result = _run(cmd, workspace)
    if result != 0:
        raise SystemExit(result)


def _iter_files(root: Path, *patterns: str) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path.is_file() and not any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
                files.append(path)
    return sorted(set(files))


def _package_scripts(workspace: Path) -> set[str]:
    package = workspace / "package.json"
    if not package.is_file():
        return set()
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid package.json: {exc}") from exc
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return set()
    return {str(name) for name in scripts}


def _ensure_node_modules(workspace: Path) -> None:
    if (workspace / "node_modules").is_dir():
        return
    cmd = ["npm", "ci"] if (workspace / "package-lock.json").is_file() else ["npm", "install"]
    _run_checked(cmd, workspace)


def _java_build_tool(workspace: Path) -> str:
    if (workspace / "pom.xml").is_file():
        return "mvn"
    if (workspace / "gradlew").is_file():
        return "./gradlew"
    if (workspace / "build.gradle").is_file() or (workspace / "build.gradle.kts").is_file():
        if shutil.which("gradle"):
            return "gradle"
        return "./gradlew"
    raise SystemExit("java project requires pom.xml, build.gradle, or build.gradle.kts")


def _lint_repo(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    for language in repo_languages(workspace):
        print(f"==> lint {language}")
        from src.services.toolkit.runner import run_cli_command

        code = run_cli_command("lint", language, workspace)
        if code != 0:
            return code
    print("repo lint ok")
    return 0


def _lint_python(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    files = _iter_files(workspace, "*.py")
    if not files:
        print("python lint skipped: no Python files")
        return 0
    return _run(["python3", "-m", "py_compile", *(str(path.relative_to(workspace)) for path in files)], workspace)


def _test_python_unit(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    return _run(
        [
            "python3",
            "-m",
            "pytest",
            "-q",
            "-m",
            "not integration",
            "--cov=src",
            "--cov-config=coverage-unit.ini",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
        ],
        workspace,
    )


def _test_python_integration(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec
    from src.services.cli_smoke import SmokeError, run_all

    config_dir = Path(extra_env["CLI_CONFIG_DIR"]) if extra_env.get("CLI_CONFIG_DIR") else None
    try:
        run_all(config_dir=config_dir, workspace=workspace)
    except SmokeError:
        return 1
    return 0


def _test_python_command_surface(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    return _test_python_integration(spec, workspace, extra_env)


def _lint_typescript(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    _ensure_node_modules(workspace)
    scripts = _package_scripts(workspace)
    for script_name in ("format:check", "lint", "typecheck"):
        if script_name in scripts:
            code = _run(["npm", "run", script_name], workspace)
            if code != 0:
                return code
    print("typescript lint ok")
    return 0


def _test_typescript_unit(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    scripts = _package_scripts(workspace)
    if "test:coverage" in scripts:
        return _run(["npm", "run", "test:coverage"], workspace)
    if "test" in scripts:
        return _run(["npm", "test"], workspace)
    print("typescript test skipped: no test script")
    return 0


def _test_typescript_build(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    if "build" not in _package_scripts(workspace):
        print("typescript build skipped: no build script")
        return 0
    return _run(["npm", "run", "build"], workspace)


def _lint_cpp(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    files = _iter_files(workspace, "*.cpp", "*.cc", "*.cxx", "*.hpp", "*.h")
    if not files:
        print("cpp lint skipped: no C++ files")
        return 0
    return _run(["clang-format", "--dry-run", "--Werror", *(str(path.relative_to(workspace)) for path in files)], workspace)


def _test_cpp_compile(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    if (workspace / "CMakeLists.txt").is_file() and shutil.which("cmake"):
        code = _run(["cmake", "-S", ".", "-B", "build"], workspace)
        if code != 0:
            return code
        return _run(["cmake", "--build", "build"], workspace)
    files = _iter_files(workspace, "*.cpp")
    if not files:
        print("cpp compile skipped: no .cpp files")
        return 0
    (workspace / "build").mkdir(exist_ok=True)
    return _run(
        ["g++", "-std=c++20", "-Wall", "-Wextra", "-pedantic", *(str(path.relative_to(workspace)) for path in files), "-o", "build/cpp-smoke"],
        workspace,
    )


def _test_cpp_smoke(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    binary = workspace / "build" / "cpp-smoke"
    if not binary.is_file():
        code = _test_cpp_compile(spec, workspace, extra_env)
        if code != 0:
            return code
    if binary.is_file():
        return _run(["./build/cpp-smoke"], workspace)
    return 0


def _lint_shell(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    files = _iter_files(workspace, "*.sh")
    if not files:
        print("shell lint skipped: no shell scripts")
        return 0
    for path in files:
        code = _run(["bash", "-n", str(path.relative_to(workspace))], workspace)
        if code != 0:
            return code
    print("shell lint ok")
    return 0


def _lint_markdown(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    if shutil.which("markdownlint-cli2") is None:
        raise SystemExit("markdownlint-cli2 is required")
    files = _iter_files(workspace, "*.md", "*.mdx")
    if not files:
        print("markdown lint skipped: no markdown files")
        return 0
    code = _run(["markdownlint-cli2", *(str(path.relative_to(workspace)) for path in files)], workspace)
    if code != 0:
        return code
    if shutil.which("mmdc") and os.environ.get("CLI_LINT_MERMAID", "1") != "0":
        _lint_mermaid_blocks(workspace, files)
    print("markdown lint ok")
    return 0


def _mermaid_puppeteer_config() -> Path | None:
    extra_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--headless",
        "--single-process",
        "--no-zygote",
    ]
    base = Path("/usr/local/share/puppeteer-no-sandbox.json")
    if base.is_file():
        data = json.loads(base.read_text(encoding="utf-8"))
    else:
        chromium = shutil.which("chromium") or shutil.which("chromium-browser")
        if not chromium:
            return None
        data = {"executablePath": chromium, "args": []}
    args = list(data.get("args") or [])
    for arg in extra_args:
        if arg not in args:
            args.append(arg)
    data["args"] = args
    config = Path(tempfile.gettempdir()) / "cli-mermaid-puppeteer.json"
    config.write_text(json.dumps(data), encoding="utf-8")
    return config


def _lint_mermaid_blocks(workspace: Path, files: list[Path]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        diagrams: list[Path] = []
        for index, file_path in enumerate(files):
            in_block = False
            block: list[str] = []
            block_index = 0
            for line in file_path.read_text(encoding="utf-8").splitlines():
                if line.strip() == "```mermaid":
                    in_block = True
                    block = []
                    block_index += 1
                    continue
                if in_block and line.strip() == "```":
                    in_block = False
                    if block:
                        diagram = tmp_dir / f"mermaid-{index}-{block_index}.mmd"
                        diagram.write_text("\n".join(block) + "\n", encoding="utf-8")
                        diagrams.append(diagram)
                    continue
                if in_block:
                    block.append(line)
        puppeteer_config = _mermaid_puppeteer_config()
        for diagram in diagrams:
            cmd = ["mmdc", "-i", str(diagram), "-o", str(diagram.with_suffix(".svg"))]
            env = os.environ.copy()
            if puppeteer_config is not None:
                cmd[1:1] = ["-p", str(puppeteer_config)]
                data = json.loads(puppeteer_config.read_text(encoding="utf-8"))
                executable = data.get("executablePath")
                if executable:
                    env["PUPPETEER_EXECUTABLE_PATH"] = str(executable)
            subprocess.run(
                cmd,
                cwd=workspace,
                check=True,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )


def _lint_java(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    tool = _java_build_tool(workspace)
    if tool == "mvn":
        return _run(["mvn", "-q", "checkstyle:check"], workspace)
    return _run([tool, "check", "--no-daemon"], workspace)


def _test_java_unit(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    tool = _java_build_tool(workspace)
    if tool == "mvn":
        return _run(["mvn", "-q", "test"], workspace)
    return _run([tool, "test", "--no-daemon"], workspace)


def _structure_check(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec
    errors: list[str] = []
    policy = None
    policy_file = extra_env.get("POLICY_FILE", "").strip()
    if policy_file:
        try:
            policy_path = Path(policy_file)
            policy = load_hygiene_policy(policy_path)
            if policy_path.is_file():
                try:
                    rel = policy_path.resolve().relative_to(workspace.resolve()).as_posix()
                    policy = policy_with_ignored_paths(policy, frozenset({rel}))
                except ValueError:
                    pass
        except (OSError, ValueError) as exc:
            errors.append(f"invalid hygiene policy: {exc}")
    errors.extend(
        check_repo_hygiene(
            workspace,
            require_layout=_env_bool(extra_env, "REQUIRE_LAYOUT") or _env_bool(extra_env, "REQUIRE_STRUCTURE"),
            require_structure=_env_bool(extra_env, "REQUIRE_STRUCTURE"),
            policy=policy,
        )
    )
    if errors:
        print("structure failed:")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print("structure ok")
    return 0


def _validate_tasks(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, extra_env
    task_root = workspace / "tasks"
    manifest = task_root / "tasks.pairs.json"
    if not manifest.is_file():
        print(f"Validation failed:\n  ERROR: task pairs manifest not found: {manifest}")
        return 1
    errors: list[str] = []
    try:
        pairs = load_pairs(manifest, task_root=task_root)
    except Exception as exc:
        print(f"Validation failed:\n  ERROR: {exc}")
        return 1
    for pair in pairs:
        warning = pair_file_warning(pair, task_root)
        if warning:
            errors.append(warning)
    errors.extend(scan_task_root(task_root).warnings)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print("OK: task pairs validation passed")
    return 0


def _languages_list(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec, workspace, extra_env
    for language in languages():
        verbs = sorted({item.group for item in specs_for_language(language)})
        print(f"{language}\t{', '.join(verbs)}")
    return 0


def _languages_show(spec: CommandSpec, workspace: Path, extra_env: dict[str, str]) -> int:
    del spec
    language = extra_env.get("CLI_LANGUAGE", "").strip()
    specs = specs_for_language(language)
    if not specs:
        print(f"Unknown language: {language}")
        return 1
    print(language)
    markers = sorted({marker for item in specs for marker in item.markers})
    bins = sorted({name for item in specs for name in item.requires_bins})
    any_bins = sorted({name for item in specs for name in item.requires_any_bins})
    if markers:
        print(f"markers: {', '.join(markers)}")
    if bins:
        print(f"requires: {', '.join(bins)}")
    if any_bins:
        print(f"requires one of: {', '.join(any_bins)}")
    print(f"workspace: {workspace}")
    for item in specs:
        suite = f" {item.suite}" if item.suite else ""
        print(f"{item.group} {item.subject}{suite}: {item.handler}")
    return 0


def _env_bool(env: dict[str, str], name: str) -> bool:
    return env.get(name, "").strip().lower() in {"1", "true", "yes", "on"}
