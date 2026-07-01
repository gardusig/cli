"""Pack tests — hub operator smoke checks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_opencode_docs_exist() -> None:
    assert (ROOT / "docs" / "opencode.md").is_file()


def test_deepseek_models_config() -> None:
    cfg = ROOT / "config" / "deepseek" / "models.yaml"
    assert cfg.is_file()
    text = cfg.read_text(encoding="utf-8")
    assert "reason" in text
    assert "chat" in text
