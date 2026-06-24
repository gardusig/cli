"""Unit tests for contest validation (mocked Docker)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from cli.services.contest_docker import RunOutcome, RunStatus
from cli.services.contest_runner import (
    ContestPaths,
    ContestValidateOptions,
    resolve_options,
    validate_contest,
)
from cli.services.contest_serde import compare_text, normalize_text, unified_diff

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "tests" / "fixtures" / "contest" / "toy"


def test_normalize_text_strips_trailing_blank_lines() -> None:
    assert normalize_text("a\nb\n\n") == "a\nb"


def test_compare_text_equal_after_normalize() -> None:
    assert compare_text("1\n2\n", "1\n2") is True
    assert compare_text("1\n2", "1\n3") is False


def test_unified_diff_on_mismatch() -> None:
    diff = unified_diff("a\nb", "a\nc")
    assert "brute" in diff
    assert "-b" in diff
    assert "+c" in diff


def test_resolve_options_from_paths() -> None:
    opts = resolve_options(
        fast=TOY / "solution.cpp",
        brute=TOY / "brute.py",
        generator=TOY / "gen.py",
        config=None,
        timeout=5.0,
        memory_mb=128,
        image="cli-contest:runner",
    )
    assert opts.timeout == 5.0
    assert opts.memory_mb == 128
    assert opts.paths.fast.name == "solution.cpp"


def test_resolve_options_missing_path() -> None:
    with pytest.raises(FileNotFoundError):
        resolve_options(
            fast=TOY / "missing.cpp",
            brute=TOY / "brute.py",
            generator=TOY / "gen.py",
            config=None,
            timeout=None,
            memory_mb=None,
            image=None,
        )


def _ok_outcome(stdout: str = "42\n") -> RunOutcome:
    return RunOutcome(RunStatus.OK, 0.1, stdout, "", 0)


def _tle_outcome() -> RunOutcome:
    return RunOutcome(RunStatus.TLE, 10.0, "", "timed out", 124)


def _make_options() -> ContestValidateOptions:
    return ContestValidateOptions(
        paths=ContestPaths(
            fast=TOY / "solution.cpp",
            brute=TOY / "brute.py",
            generator=TOY / "gen.py",
        ),
        timeout=10.0,
        memory_mb=256,
    )


@patch("cli.services.contest_runner.ensure_contest_image")
@patch("cli.services.contest_runner.compile_fast_solution")
@patch("cli.services.contest_runner.run_fast")
@patch("cli.services.contest_runner.run_brute")
def test_validate_pass_small_match_large_tle(
    mock_brute,
    mock_fast,
    mock_compile,
    mock_ensure_image,
) -> None:
    mock_compile.return_value = _ok_outcome()
    small_out = "10\n30\n"
    mock_brute.side_effect = [_ok_outcome(small_out), _tle_outcome()]
    mock_fast.side_effect = [_ok_outcome(small_out), _ok_outcome("10125375\n")]

    result = validate_contest(_make_options())

    assert result.passed is True
    assert result.small is not None
    assert result.small.outputs_match is True
    assert result.large is not None
    assert result.large.brute.status == RunStatus.TLE
    assert result.large.fast.status == RunStatus.OK
    assert result.warnings == []
    assert mock_brute.call_count == 2
    assert mock_fast.call_count == 2


@patch("cli.services.contest_runner.ensure_contest_image")
@patch("cli.services.contest_runner.compile_fast_solution")
@patch("cli.services.contest_runner.run_fast")
@patch("cli.services.contest_runner.run_brute")
def test_validate_small_mismatch_skips_large(
    mock_brute,
    mock_fast,
    mock_compile,
    mock_ensure_image,
) -> None:
    mock_compile.return_value = _ok_outcome()
    mock_brute.return_value = _ok_outcome("1\n")
    mock_fast.return_value = _ok_outcome("2\n")

    result = validate_contest(_make_options())

    assert result.passed is False
    assert result.small is not None
    assert result.small.outputs_match is False
    assert result.large is None
    assert result.small_diff is not None
    assert mock_brute.call_count == 1
    assert mock_fast.call_count == 1


@patch("cli.services.contest_runner.ensure_contest_image")
@patch("cli.services.contest_runner.compile_fast_solution")
@patch("cli.services.contest_runner.run_fast")
@patch("cli.services.contest_runner.run_brute")
def test_validate_large_brute_ok_emits_warning(
    mock_brute,
    mock_fast,
    mock_compile,
    mock_ensure_image,
) -> None:
    mock_compile.return_value = _ok_outcome()
    matched = "5\n"
    mock_brute.side_effect = [_ok_outcome(matched), _ok_outcome("999\n")]
    mock_fast.side_effect = [_ok_outcome(matched), _ok_outcome("999\n")]

    result = validate_contest(_make_options())

    assert result.passed is True
    assert len(result.warnings) == 1
    assert "stress" in result.warnings[0].lower()


@patch("cli.services.contest_runner.ensure_contest_image")
@patch("cli.services.contest_runner.compile_fast_solution")
def test_validate_compile_error(mock_compile, mock_ensure_image) -> None:
    mock_compile.return_value = RunOutcome(
        RunStatus.COMPILE_ERROR, 0.5, "", "error: expected ';'", 1
    )

    result = validate_contest(_make_options())

    assert result.passed is False
    assert result.error is not None
    assert "compile" in result.error.lower()


@patch("cli.services.contest_runner.ensure_contest_image")
@patch("cli.services.contest_runner.compile_fast_solution")
@patch("cli.services.contest_runner.run_fast")
@patch("cli.services.contest_runner.run_brute")
def test_validate_fast_tle_on_large_fails(
    mock_brute,
    mock_fast,
    mock_compile,
    mock_ensure_image,
) -> None:
    mock_compile.return_value = _ok_outcome()
    matched = "1\n"
    mock_brute.side_effect = [_ok_outcome(matched), _tle_outcome()]
    mock_fast.side_effect = [_ok_outcome(matched), _tle_outcome()]

    result = validate_contest(_make_options())

    assert result.passed is False
    assert result.large is not None
    assert "large" in (result.error or "").lower()
