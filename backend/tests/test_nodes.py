"""Tests for LangGraph nodes (Task 3.2.1–3.2.5)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.state import make_initial_state


# ── ヘルパー ──────────────────────────────────────────────────────────────────

def make_state_with_metrics(**overrides):
    state = make_initial_state(session_id="test", weight_mode="fixed")
    state["raw_metrics"] = {
        "face": {"happy": 0.5, "angry": 0.1, "sad": 0.1, "neutral": 0.3, "stability": 0.8},
        "voice": {
            "rms_mean": 0.3, "rms_std": 0.05,
            "pitch_mean": 180.0, "pitch_std": 20.0,
            "speech_rate": 4.0, "silence_duration": 1.0,
        },
        "text": {
            "interval_ms": 120.0, "backspace_count": 2,
            "total_keys": 40, "idle_ms": 500.0, "total_time_ms": 6000.0,
        },
        "face_quality": 0.9,
        "voice_quality": 0.8,
        "text_quality": 0.7,
    }
    state.update(overrides)
    return state


# ── Task 3.2.1: question_node ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_question_node_adds_ai_message_to_history():
    """question_node は AIMessage を history に追加する"""
    mock_resp = MagicMock()
    mock_resp.text = "最近、気になっていることはありますか？"

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
        from app.agents.nodes.question_node import question_node
        state = make_initial_state(session_id="test", weight_mode="fixed")
        result = await question_node(state)

    assert "history" in result
    assert len(result["history"]) == 1
    assert isinstance(result["history"][0], AIMessage)


@pytest.mark.asyncio
async def test_question_node_increments_turn_count():
    """question_node は turn_count を +1 する"""
    mock_resp = MagicMock()
    mock_resp.text = "今日はどんな一日でしたか？"

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
        from app.agents.nodes.question_node import question_node
        state = make_initial_state(session_id="test", weight_mode="fixed")
        state["turn_count"] = 2
        result = await question_node(state)

    assert result["turn_count"] == 3


# ── Task 3.2.2: analysis_node ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analysis_node_updates_mental_state():
    """analysis_node は mental_state を A/B/C/D-1/D-2 に更新する"""
    from app.agents.nodes.analysis_node import analysis_node
    state = make_state_with_metrics()
    result = await analysis_node(state)

    assert result["mental_state"] in {"A", "B", "C", "D-1", "D-2"}


@pytest.mark.asyncio
async def test_analysis_node_updates_score_breakdown():
    """analysis_node は score_breakdown に contributions を含む"""
    from app.agents.nodes.analysis_node import analysis_node
    state = make_state_with_metrics()
    result = await analysis_node(state)

    assert "score_breakdown" in result
    assert "contributions" in result["score_breakdown"]
    assert "weights" in result["score_breakdown"]


@pytest.mark.asyncio
async def test_analysis_node_mental_score_in_range():
    """mental_score は 0.0–1.0 の範囲"""
    from app.agents.nodes.analysis_node import analysis_node
    state = make_state_with_metrics()
    result = await analysis_node(state)

    assert 0.0 <= result["mental_score"] <= 1.0


@pytest.mark.asyncio
async def test_analysis_node_with_empty_metrics_uses_defaults():
    """raw_metrics が空でもクラッシュしない"""
    from app.agents.nodes.analysis_node import analysis_node
    state = make_initial_state(session_id="test", weight_mode="fixed")
    state["raw_metrics"] = {}
    result = await analysis_node(state)

    assert "mental_state" in result
    assert "mental_score" in result


# ── Task 3.2.3: reasoning_node ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reasoning_node_updates_reasoning():
    """reasoning_node は reasoning を文字列で更新する"""
    mock_resp = MagicMock()
    mock_resp.text = "表情から落ち着いた様子が見られます。"

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
        from app.agents.nodes.reasoning_node import reasoning_node
        state = make_state_with_metrics()
        state["score_breakdown"] = {
            "score": 0.6,
            "contributions": {"face": 0.21, "voice": 0.27, "text": 0.12},
            "weights": {"face": 0.35, "voice": 0.45, "text": 0.20},
        }
        result = await reasoning_node(state)

    assert "reasoning" in result
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"]) > 0


# ── Task 3.2.4: routing_node ──────────────────────────────────────────────────

def test_routing_returns_question_when_turns_remain():
    """ターンが残っていれば 'question' を返す"""
    from app.agents.nodes.routing_node import routing_node
    state = make_state_with_metrics(turn_count=3, mental_state="B")
    result = routing_node(state, max_turns=10)
    assert result == "question"


def test_routing_returns_close_when_max_turns_reached():
    """max_turns に達したら 'close' を返す"""
    from app.agents.nodes.routing_node import routing_node
    state = make_state_with_metrics(turn_count=10, mental_state="B")
    result = routing_node(state, max_turns=10)
    assert result == "close"


def test_routing_returns_close_for_d1_state():
    """D-1 状態は 'close' を返す"""
    from app.agents.nodes.routing_node import routing_node
    state = make_state_with_metrics(turn_count=2, mental_state="D-1")
    result = routing_node(state, max_turns=10)
    assert result == "close"


def test_routing_returns_close_for_d2_state():
    """D-2 状態は 'close' を返す"""
    from app.agents.nodes.routing_node import routing_node
    state = make_state_with_metrics(turn_count=2, mental_state="D-2")
    result = routing_node(state, max_turns=10)
    assert result == "close"


# ── Task 3.2.5: close_node ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_close_node_returns_state_update():
    """close_node は dict を返す"""
    from app.agents.nodes.close_node import close_node
    state = make_state_with_metrics(turn_count=5, mental_state="B")
    result = await close_node(state)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_close_node_sets_final_flag():
    """close_node は raw_metrics に done フラグを立てる"""
    from app.agents.nodes.close_node import close_node
    state = make_state_with_metrics(turn_count=5, mental_state="C")
    result = await close_node(state)
    assert result.get("raw_metrics", {}).get("done") is True
