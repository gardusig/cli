"""Chat session storage tests."""

from __future__ import annotations

import json

import pytest

from src.services.chat_session import ChatSession, chat_root


@pytest.fixture
def chat_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("CLI_CHAT_DIR", str(tmp_path))
    return tmp_path


def test_session_create_append_and_summary(chat_dir) -> None:
    s = ChatSession.create("test-1")
    s.append("user", "idea about cli hub")
    s.append("assistant", "noted")
    assert len(s.messages()) == 2
    s.set_summary("- cli hub idea")
    assert "cli hub" in s.summary()


def test_export_bundle(chat_dir) -> None:
    s = ChatSession.create("test-2")
    s.append("user", "hello")
    bundle = s.export_bundle()
    assert bundle["session_id"] == "test-2"
    assert "hello" in bundle["transcript"]


def test_list_sessions(chat_dir) -> None:
    ChatSession.create("a")
    ChatSession.create("b")
    assert "a" in ChatSession.list_sessions()
    assert chat_root() == chat_dir
