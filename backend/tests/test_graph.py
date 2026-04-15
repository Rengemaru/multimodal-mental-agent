"""Tests for LangGraph StateGraph (Task 3.3)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.state import make_initial_state


# ── グラフ構造 ────────────────────────────────────────────────────────────────

def test_build_graph_returns_compiled_graph():
    """build_graph() がコンパイル済みグラフを返す"""
    from app.agents.graph import build_graph
    graph = build_graph()
    assert graph is not None


def test_graph_has_all_nodes():
    """graph に全ノードが登録されている"""
    from app.agents.graph import build_graph
    graph = build_graph()
    nodes = set(graph.get_graph().nodes.keys())
    for expected in ("analysis", "reasoning", "question", "close"):
        assert expected in nodes, f"node '{expected}' not found in graph"


def test_graph_mermaid_output():
    """get_graph().draw_mermaid() が文字列を返す (受け入れ基準)"""
    from app.agents.graph import build_graph
    graph = build_graph()
    mermaid = graph.get_graph().draw_mermaid()
    assert isinstance(mermaid, str)
    assert len(mermaid) > 0


# ── end-to-end 実行 ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_graph_runs_to_question_node():
    """通常フローで question ノードまで到達して END する"""
    mock_resp = MagicMock()
    mock_resp.text = "最近どんなことがありましたか？"

    state = make_initial_state(session_id="e2e-test", weight_mode="fixed")
    state["raw_metrics"] = {
        "face": {"happy": 0.6, "angry": 0.05, "sad": 0.05, "neutral": 0.3, "stability": 0.9},
        "voice": {
            "rms_mean": 0.3, "rms_std": 0.04,
            "pitch_mean": 175.0, "pitch_std": 18.0,
            "speech_rate": 3.8, "silence_duration": 1.2,
        },
        "text": {
            "interval_ms": 110.0, "backspace_count": 1,
            "total_keys": 35, "idle_ms": 400.0, "total_time_ms": 5000.0,
        },
        "face_quality": 0.9,
        "voice_quality": 0.8,
        "text_quality": 0.7,
    }

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
        from app.agents.graph import build_graph
        graph = build_graph()
        result = await graph.ainvoke(state)

    assert "mental_state" in result
    assert result["mental_state"] in {"A", "B", "C", "D-1", "D-2"}
    assert "reasoning" in result
    assert isinstance(result["reasoning"], str)


@pytest.mark.asyncio
async def test_graph_runs_to_close_node_at_max_turns():
    """max_turns に達すると close ノードで終了する"""
    mock_resp = MagicMock()
    mock_resp.text = "お疲れさまでした。"

    state = make_initial_state(session_id="e2e-close", weight_mode="fixed")
    state["turn_count"] = 10   # MAX_TURNS デフォルト値
    state["raw_metrics"] = {
        "face": {"happy": 0.4, "angry": 0.1, "sad": 0.1, "neutral": 0.4, "stability": 0.7},
        "voice": {
            "rms_mean": 0.25, "rms_std": 0.06,
            "pitch_mean": 165.0, "pitch_std": 22.0,
            "speech_rate": 4.2, "silence_duration": 1.5,
        },
        "text": {
            "interval_ms": 130.0, "backspace_count": 3,
            "total_keys": 30, "idle_ms": 800.0, "total_time_ms": 7000.0,
        },
    }

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)
        from app.agents.graph import build_graph
        graph = build_graph()
        result = await graph.ainvoke(state)

    assert result.get("raw_metrics", {}).get("done") is True
