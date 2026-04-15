"""Tests for AgentState definition (Task 3.1)."""

import pytest


def test_agent_state_has_required_fields():
    """AgentState が必須フィールドを全て持つ"""
    from app.agents.state import AgentState
    state: AgentState = {
        "session_id": "test-001",
        "turn_count": 0,
        "mental_state": "B",
        "mental_score": 0.6,
        "score_breakdown": {},
        "reasoning": "",
        "weights_used": {"face": 0.35, "voice": 0.45, "text": 0.20},
        "weight_mode": "fixed",
        "history": [],
        "raw_metrics": {},
        "self_report": {},
    }
    assert state["session_id"] == "test-001"
    assert state["turn_count"] == 0


def test_agent_state_weight_mode_values():
    """weight_mode に fixed / dynamic / learned を設定できる"""
    from app.agents.state import AgentState
    for mode in ("fixed", "dynamic", "learned"):
        state: AgentState = {
            "session_id": "x",
            "turn_count": 0,
            "mental_state": "A",
            "mental_score": 0.8,
            "score_breakdown": {},
            "reasoning": "",
            "weights_used": {},
            "weight_mode": mode,
            "history": [],
            "raw_metrics": {},
            "self_report": {},
        }
        assert state["weight_mode"] == mode


def test_agent_state_score_breakdown_contains_contributions():
    """score_breakdown に contributions / weights / score を格納できる"""
    from app.agents.state import AgentState
    breakdown = {
        "score": 0.65,
        "contributions": {"face": 0.23, "voice": 0.29, "text": 0.13},
        "weights": {"face": 0.35, "voice": 0.45, "text": 0.20},
    }
    state: AgentState = {
        "session_id": "x",
        "turn_count": 1,
        "mental_state": "B",
        "mental_score": 0.65,
        "score_breakdown": breakdown,
        "reasoning": "音声から落ち着いた様子が見られます。",
        "weights_used": breakdown["weights"],
        "weight_mode": "fixed",
        "history": [],
        "raw_metrics": {},
        "self_report": {"pre_session": 0.6},
    }
    assert state["score_breakdown"]["score"] == 0.65
    assert "contributions" in state["score_breakdown"]


def test_agent_state_history_accepts_messages():
    """history に langchain_core の BaseMessage を格納できる"""
    from langchain_core.messages import HumanMessage, AIMessage
    from app.agents.state import AgentState
    state: AgentState = {
        "session_id": "x",
        "turn_count": 2,
        "mental_state": "B",
        "mental_score": 0.6,
        "score_breakdown": {},
        "reasoning": "",
        "weights_used": {},
        "weight_mode": "fixed",
        "history": [
            HumanMessage(content="こんにちは"),
            AIMessage(content="こんにちは。最近どうですか？"),
        ],
        "raw_metrics": {},
        "self_report": {},
    }
    assert len(state["history"]) == 2


def test_initial_state_factory_returns_valid_state():
    """make_initial_state() が有効な AgentState を返す"""
    from app.agents.state import make_initial_state
    state = make_initial_state(session_id="sess-abc", weight_mode="fixed")
    assert state["session_id"] == "sess-abc"
    assert state["turn_count"] == 0
    assert state["weight_mode"] == "fixed"
    assert state["history"] == []
    assert state["mental_score"] == 0.5
