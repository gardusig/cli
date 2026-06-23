"""Shell scripts stay thin — no embedded Python in scripts/."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def test_scripts_tree_has_no_embedded_python() -> None:
    for path in SCRIPTS.rglob("*.sh"):
        text = path.read_text(encoding="utf-8")
        assert "<<'PY'" not in text, f"embedded Python heredoc in {path.relative_to(ROOT)}"
        assert 'python3 - <<' not in text, f"embedded Python in {path.relative_to(ROOT)}"


def test_shared_common_is_sourced() -> None:
    for rel in (
        "git/_common.sh",
        "docker/_common.sh",
        "gh/_common.sh",
    ):
        text = (SCRIPTS / rel).read_text(encoding="utf-8")
        assert "_common.sh" in text
