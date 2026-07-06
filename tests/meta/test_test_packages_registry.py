"""Registry completeness for selective CI test packages."""

from __future__ import annotations

from src.services.test_packages import (
    TEST_PACKAGES,
    _PACKAGE_INTEGRATION,
    package_names,
)


def test_every_package_has_unit_tests() -> None:
    missing = [pkg.name for pkg in TEST_PACKAGES if not pkg.unit_test_paths]
    assert missing == [], f"packages without unit_test_paths: {missing}"


def test_runner_packages_use_package_integration() -> None:
    from src.integration.package_integration import runner_packages

    for name in runner_packages():
        pkg = next(p for p in TEST_PACKAGES if p.name == name)
        assert _PACKAGE_INTEGRATION in pkg.integration_checks, name


def test_package_names_are_unique() -> None:
    names = [pkg.name for pkg in TEST_PACKAGES]
    assert len(names) == len(set(names))


def test_registry_includes_public_packages() -> None:
    for name in ("git", "gh", "docker", "notion", "drive", "chrome", "contest", "project"):
        assert name in package_names()


def test_registry_tuple_is_stable_order() -> None:
    from src.services.test_packages import test_package_registry

    assert test_package_registry() == TEST_PACKAGES
