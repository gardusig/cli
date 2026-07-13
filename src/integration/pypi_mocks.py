"""Mock PyPI build/publish calls during endpoint unit checks."""

from __future__ import annotations

from contextlib import AbstractContextManager, ExitStack, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from src.integration.public_endpoints import EndpointCheck


def pypi_endpoint_needs_mock(check: EndpointCheck) -> bool:
    if not check.args:
        return False
    if check.args[0] not in {"pypi", "publish"}:
        return False
    if check.failure in {"missing_pyproject", "missing_pypi_token", "version_not_increased"}:
        return False
    if check.kind == "refuse":
        return False
    return True


def pypi_endpoint_patches(check: EndpointCheck) -> AbstractContextManager[object]:
    if not pypi_endpoint_needs_mock(check):
        return nullcontext()

    stack = ExitStack()
    artifact = Path("dist/pkg.whl")
    if check.args[0] in {"pypi", "publish"} and (
        check.args[0] == "publish"
        or len(check.args) > 1
        and check.args[1] in {"build", "upload"}
    ):
        stack.enter_context(
            patch("src.commands.pypi.build_distributions", return_value=[artifact]),
        )
    if check.args[0] == "pypi" and len(check.args) > 1 and check.args[1] == "upload":
        stack.enter_context(
            patch("src.commands.pypi.publish_distributions", return_value=["pkg.whl"]),
        )
        stack.enter_context(patch("src.commands.pypi.verify_package_version_on_index"))
        stack.enter_context(patch("src.commands.pypi.resolve_pypi_token", return_value="tok"))
    if check.args[:3] == ("pypi", "version", "suggest"):
        stack.enter_context(
            patch("src.commands.pypi.suggest_next_release_version", return_value="1.0.7"),
        )
    if check.args[:3] == ("pypi", "version", "set"):
        stack.enter_context(
            patch("src.commands.pypi.suggest_next_release_version", return_value="1.0.7"),
        )
        if "--dry-run" not in check.args:
            stack.enter_context(
                patch("src.commands.pypi.apply_next_release_version", return_value="1.0.7"),
            )
    if check.args[:3] == ("pypi", "version", "tag-suggest"):
        stack.enter_context(patch("src.commands.pypi.suggest_next_tag", return_value="v1.0.7"))
    return stack
