"""Expand pipeline job graphs from `cli test packages resolve` output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.services.test_packages import changed_paths_from_git, package_resolution_payload


def selective_resolution(
    *,
    app_src: Path,
    base: str,
    head: str,
    package_limit: int = 4,
) -> dict[str, Any]:
    paths = changed_paths_from_git(base, head, app_src)
    return package_resolution_payload(paths, package_limit=package_limit)


def apply_selective_jobs(
    jobs: dict[str, dict[str, Any]],
    *,
    cfg: dict[str, Any],
    app_src: Path | None,
    selective_base: str,
    selective_head: str,
    force_full_suite: bool = False,
) -> dict[str, dict[str, Any]]:
    """Rewrite job map for selective CI when config declares `selective: true`."""
    if not cfg.get("selective") or app_src is None or not selective_base or not selective_head:
        return jobs

    if not isinstance(app_src, Path):
        app_src = Path(app_src)

    if force_full_suite:
        full_suite = True
        package_names: list[str] = []
    else:
        resolution = selective_resolution(
            app_src=app_src,
            base=selective_base,
            head=selective_head,
        )
        full_suite = bool(resolution.get("full_suite"))
        package_names = list(resolution.get("package_names") or [])

    result: dict[str, dict[str, Any]] = {}
    matrix_unit_ids: list[str] = []
    matrix_integration_ids: list[str] = []

    for jid, job in jobs.items():
        when_full_suite = bool(job.get("when_full_suite"))
        if full_suite and not when_full_suite and job.get("matrix"):
            continue
        if not full_suite and when_full_suite:
            continue

        matrix_kind = job.get("matrix")
        if not full_suite and matrix_kind in {"unit", "integration"}:
            for package in package_names:
                suffix = "unit" if matrix_kind == "unit" else "integration"
                expanded_id = f"{suffix}-{package}"
                expanded = dict(job)
                expanded["id"] = expanded_id
                expanded["name"] = f"{job.get('name') or jid} ({package})"
                expanded.pop("matrix", None)
                build_args = dict(expanded.get("build_args") or {})
                build_args["PACKAGE"] = package
                expanded["build_args"] = build_args
                if matrix_kind == "integration" and package == "docker":
                    expanded["docker_socket"] = True
                result[expanded_id] = expanded
                if matrix_kind == "unit":
                    matrix_unit_ids.append(expanded_id)
                else:
                    matrix_integration_ids.append(expanded_id)
            continue

        result[jid] = dict(job)

    if not full_suite and matrix_integration_ids:
        result["test-gate"] = {
            "id": "test-gate",
            "name": "Selective tests complete",
            "target": "selective-gate",
            "needs": matrix_integration_ids,
        }
        for jid, job in list(result.items()):
            if jid == "pypi" or jid == "testpypi-consumer":
                needs = list(_as_list(job.get("needs")))
                needs = [dep for dep in needs if dep not in {"unit", "package-unit", "package-integration", "integration"}]
                needs.append("test-gate")
                job["needs"] = sorted(set(needs))
    elif full_suite:
        for jid, job in list(result.items()):
            if jid in {"pypi", "testpypi-consumer"}:
                needs = list(_as_list(job.get("needs")))
                if "unit" not in needs and "integration" not in needs:
                    needs.append("unit")
                job["needs"] = needs

    return result


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
