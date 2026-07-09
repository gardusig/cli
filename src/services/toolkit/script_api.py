from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.services.notion_pairs import load_pairs, pair_file_warning, scan_task_root
from src.services.repo_hygiene import check_repo_hygiene, load_hygiene_policy, policy_with_ignored_paths
from src.services.toolkit.catalog import languages, specs_for_language


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m src.services.toolkit.script_api")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("structure-check")
    sub.add_parser("validate-tasks")
    sub.add_parser("languages-list")
    show = sub.add_parser("languages-show")
    show.add_argument("language")
    args = parser.parse_args()
    workspace = Path(os.environ.get("WORKSPACE", ".")).expanduser().resolve()
    if args.command == "structure-check":
        _structure_check(workspace)
    elif args.command == "validate-tasks":
        _validate_tasks(workspace)
    elif args.command == "languages-list":
        _languages_list()
    elif args.command == "languages-show":
        _languages_show(args.language, workspace)


def _structure_check(workspace: Path) -> None:
    errors: list[str] = []
    policy = None
    policy_file = os.environ.get("POLICY_FILE", "").strip()
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
            require_layout=_env_bool("REQUIRE_LAYOUT") or _env_bool("REQUIRE_STRUCTURE"),
            require_structure=_env_bool("REQUIRE_STRUCTURE"),
            policy=policy,
        )
    )
    if errors:
        print("structure failed:")
        for error in errors:
            print(f"  ERROR: {error}")
        raise SystemExit(1)
    print("structure ok")


def _validate_tasks(workspace: Path) -> None:
    task_root = workspace / "tasks"
    manifest = task_root / "tasks.pairs.json"
    if not manifest.is_file():
        print(f"Validation failed:\n  ERROR: task pairs manifest not found: {manifest}")
        raise SystemExit(1)
    errors: list[str] = []
    try:
        pairs = load_pairs(manifest, task_root=task_root)
    except Exception as exc:
        print(f"Validation failed:\n  ERROR: {exc}")
        raise SystemExit(1)
    for pair in pairs:
        warning = pair_file_warning(pair, task_root)
        if warning:
            errors.append(warning)
    errors.extend(scan_task_root(task_root).warnings)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  ERROR: {error}")
        raise SystemExit(1)
    print("OK: task pairs validation passed")


def _languages_list() -> None:
    for language in languages():
        verbs = sorted({spec.group for spec in specs_for_language(language)})
        print(f"{language}\t{', '.join(verbs)}")


def _languages_show(language: str, workspace: Path) -> None:
    specs = specs_for_language(language)
    if not specs:
        print(f"Unknown language: {language}")
        raise SystemExit(1)
    print(f"{language}")
    markers = sorted({marker for spec in specs for marker in spec.markers})
    bins = sorted({name for spec in specs for name in spec.requires_bins})
    any_bins = sorted({name for spec in specs for name in spec.requires_any_bins})
    if markers:
        print(f"markers: {', '.join(markers)}")
    if bins:
        print(f"requires: {', '.join(bins)}")
    if any_bins:
        print(f"requires one of: {', '.join(any_bins)}")
    print(f"workspace: {workspace}")
    for spec in specs:
        suite = f" {spec.suite}" if spec.suite else ""
        print(f"{spec.group} {spec.subject}{suite}: {spec.handler}")


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    main()
