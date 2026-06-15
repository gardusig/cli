"""Tests for notion markdown conversion."""

from shuttle.services.notion_markdown import blocks_to_markdown, markdown_to_blocks


def test_markdown_round_trip_headings_and_todos() -> None:
    md = (
        "## Steps\n\n"
        "1. First\n\n"
        "## Done when\n\n"
        "- [ ] Item one\n"
        "- [x] Item two\n"
    )
    blocks = markdown_to_blocks(md)
    assert not any(b["type"] == "heading_1" for b in blocks)
    assert any(b["type"] == "heading_2" for b in blocks)
    assert any(b["type"] == "to_do" for b in blocks)
    out = blocks_to_markdown(blocks)
    assert out.startswith("## Steps")
    assert "- [ ] Item one" in out
    assert "- [x] Item two" in out
