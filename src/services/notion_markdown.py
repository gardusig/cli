"""Minimal markdown ↔ Notion block conversion for task bodies."""

from __future__ import annotations

import re

_TODO_RE = re.compile(r"^-\s+\[([ xX])\]\s+(.*)$")


_H1_RE = re.compile(r"^#\s+.+$")


_STEPS_HEADING = "## Steps"


def strip_content_before_steps(markdown: str) -> str:
    """Drop intro/cadence prose — body starts at ## Steps."""
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == _STEPS_HEADING:
            body = "\n".join(lines[i:]).strip()
            return body + ("\n" if body else "")
    return markdown.strip() + ("\n" if markdown.strip() else "")


def normalize_task_body(markdown: str) -> str:
    """Task body for git: no title, no cadence intro — Steps onward only."""
    return strip_content_before_steps(strip_leading_title_heading(markdown))


def strip_leading_title_heading(markdown: str) -> str:
    """Remove a leading H1 line (task title belongs in metadata.name, not body)."""
    lines = markdown.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and _H1_RE.match(lines[0].strip()):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip() + ("\n" if lines else "")


def blocks_to_task_body(blocks: list[dict], *, task_name: str = "") -> str:
    """Convert Notion blocks to body markdown (Steps section onward only)."""
    content = list(blocks)
    if content and content[0].get("type") == "heading_1":
        heading = _rich_text_plain(content[0]["heading_1"]["rich_text"])
        if not task_name or heading.casefold() == task_name.casefold():
            content = content[1:]
        elif _looks_like_title_heading(heading, task_name):
            content = content[1:]
    content = _trim_blocks_before_steps(content)
    return normalize_task_body(blocks_to_markdown(content))


def _trim_blocks_before_steps(blocks: list[dict]) -> list[dict]:
    for i, block in enumerate(blocks):
        if block.get("type") != "heading_2":
            continue
        heading = _rich_text_plain(block["heading_2"]["rich_text"])
        if heading.casefold() == "steps":
            return blocks[i:]
    return blocks


def _looks_like_title_heading(heading: str, task_name: str) -> bool:
    if not task_name:
        return True
    h = heading.casefold().strip()
    n = task_name.casefold().strip()
    return h in n or n in h


def markdown_to_blocks(markdown: str) -> list[dict]:
    """Convert task body markdown to Notion block payloads (no H1 — title is a property)."""
    markdown = normalize_task_body(markdown)
    blocks: list[dict] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        text = "\n".join(paragraph_lines).strip()
        if text:
            blocks.append(_paragraph_block(text))
        paragraph_lines.clear()

    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith("# "):
            # Task title is metadata.name — skip duplicate H1 in body.
            flush_paragraph()
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            blocks.append(_heading_block(2, stripped[3:].strip()))
            continue
        todo = _TODO_RE.match(stripped)
        if todo:
            flush_paragraph()
            checked = todo.group(1).lower() == "x"
            blocks.append(_todo_block(todo.group(2).strip(), checked))
            continue
        paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def blocks_to_markdown(blocks: list[dict]) -> str:
    """Convert Notion blocks to task body markdown."""
    lines: list[str] = []
    for block in blocks:
        kind = block.get("type")
        if kind == "heading_1":
            lines.append(f"# {_rich_text_plain(block['heading_1']['rich_text'])}")
        elif kind == "heading_2":
            lines.append(f"## {_rich_text_plain(block['heading_2']['rich_text'])}")
        elif kind == "paragraph":
            text = _rich_text_plain(block["paragraph"]["rich_text"])
            if text:
                lines.append(text)
        elif kind == "to_do":
            checked = block["to_do"].get("checked", False)
            mark = "x" if checked else " "
            text = _rich_text_plain(block["to_do"]["rich_text"])
            lines.append(f"- [{mark}] {text}")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def _rich_text_plain(rich_text: list[dict]) -> str:
    parts: list[str] = []
    for part in rich_text:
        if part.get("plain_text"):
            parts.append(part["plain_text"])
        elif part.get("type") == "text":
            parts.append(part.get("text", {}).get("content", ""))
    return "".join(parts)


def _paragraph_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [_text_chunk(text)]},
    }


def _heading_block(level: int, text: str) -> dict:
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {"rich_text": [_text_chunk(text)]},
    }


def _todo_block(text: str, checked: bool) -> dict:
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [_text_chunk(text)],
            "checked": checked,
        },
    }


def _text_chunk(text: str) -> dict:
    return {"type": "text", "text": {"content": text}}
