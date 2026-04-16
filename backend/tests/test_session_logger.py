"""Tests for session log saving (Task 4.2)."""

import json
import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.services.session_logger import build_turns, save_session_log


def make_state(session_id: str = "sess-001", turns_n: int = 2) -> dict:
    """Build a minimal AgentState-like dict for testing."""
    history = []
    for i in range(turns_n):
        history.append(HumanMessage(content=f"answer {i + 1}"))
        history.append(AIMessage(content=f"question {i + 1}"))
    return {
        "session_id": session_id,
        "turn_count": turns_n,
        "mental_state": "B",
        "mental_score": 0.65,
        "score_breakdown": {"score": 0.65, "contributions": {}},
        "reasoning": "落ち着いた様子",
        "weights_used": {"face": 0.35, "voice": 0.45, "text": 0.20},
        "weight_mode": "fixed",
        "history": history,
        "raw_metrics": {"done": True},
        "self_report": {"pre_session": 0.6, "post_session": 0.7},
    }


# ── build_turns ───────────────────────────────────────────────────────────────

def test_build_turns_returns_correct_count():
    turns = build_turns(make_state(turns_n=3))
    assert len(turns) == 3


def test_build_turns_pairs_messages_correctly():
    turns = build_turns(make_state(turns_n=2))
    assert turns[0].answer == "answer 1"
    assert turns[0].question == "question 1"
    assert turns[1].answer == "answer 2"
    assert turns[1].question == "question 2"


def test_build_turns_has_mental_state_fields():
    turns = build_turns(make_state(turns_n=1))
    assert turns[0].mental_state == "B"
    assert turns[0].mental_score == 0.65


def test_build_turns_empty_history():
    turns = build_turns(make_state(turns_n=0))
    assert turns == []


def test_build_turns_human_without_following_ai():
    """末尾に AIMessage がない HumanMessage も処理できる。"""
    state = make_state(turns_n=0)
    state["history"] = [HumanMessage(content="last answer")]
    turns = build_turns(state)
    assert len(turns) == 1
    assert turns[0].answer == "last answer"
    assert turns[0].question == ""


# ── save_session_log ──────────────────────────────────────────────────────────

def test_save_session_log_creates_file(tmp_path):
    filepath = save_session_log(make_state(), data_dir=tmp_path)
    assert filepath.exists()


def test_save_session_log_filename_format(tmp_path):
    filepath = save_session_log(make_state(session_id="test-session"), data_dir=tmp_path)
    assert filepath.name.startswith("test-session_")
    assert filepath.suffix == ".json"


def test_save_session_log_json_has_required_fields(tmp_path):
    filepath = save_session_log(
        make_state(), data_dir=tmp_path, subject_id="S001", consent_version="v1.0"
    )
    data = json.loads(filepath.read_text(encoding="utf-8"))
    assert data["session_id"] == "sess-001"
    assert data["subject_id"] == "S001"
    assert data["consent_version"] == "v1.0"
    assert "self_report" in data
    assert "weights_used" in data
    assert "weight_mode" in data
    assert "turns" in data


def test_save_session_log_turns_content(tmp_path):
    filepath = save_session_log(make_state(turns_n=2), data_dir=tmp_path)
    data = json.loads(filepath.read_text(encoding="utf-8"))
    assert len(data["turns"]) == 2
    assert data["turns"][0]["answer"] == "answer 1"
    assert data["turns"][0]["question"] == "question 1"


def test_save_session_log_creates_nested_directory(tmp_path):
    """存在しないディレクトリも自動生成される。"""
    nested_dir = tmp_path / "deep" / "sessions"
    filepath = save_session_log(make_state(), data_dir=nested_dir)
    assert nested_dir.exists()
    assert filepath.exists()


def test_save_session_log_self_report_saved(tmp_path):
    filepath = save_session_log(make_state(), data_dir=tmp_path)
    data = json.loads(filepath.read_text(encoding="utf-8"))
    assert data["self_report"]["pre_session"] == pytest.approx(0.6)
    assert data["self_report"]["post_session"] == pytest.approx(0.7)


def test_build_turns_skips_leading_ai_message():
    """history の先頭が AIMessage の場合はスキップして次を処理する。"""
    state = make_state(turns_n=0)
    state["history"] = [
        AIMessage(content="先頭のAIメッセージ"),  # ← session_logger.py:44 の else ブランチ
        HumanMessage(content="ユーザー回答"),
        AIMessage(content="次の質問"),
    ]
    turns = build_turns(state)
    assert len(turns) == 1
    assert turns[0].answer == "ユーザー回答"
    assert turns[0].question == "次の質問"
