from __future__ import annotations

import shutil


class ToolkitPrereqError(RuntimeError):
    pass


def check_prereqs(requires_bins: tuple[str, ...], requires_any_bins: tuple[str, ...]) -> None:
    missing = [name for name in requires_bins if shutil.which(name) is None]
    if missing:
        raise ToolkitPrereqError(f"missing required executable(s): {', '.join(missing)}")
    if requires_any_bins and not any(shutil.which(name) for name in requires_any_bins):
        raise ToolkitPrereqError(f"missing one of required executable(s): {', '.join(requires_any_bins)}")

