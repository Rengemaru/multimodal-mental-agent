"""Task 8.2: E2E session flow test.

Full session lifecycle over WebSocket:
  connect → self_report(pre) → face/text events → message × N turns
  → self_report(post) → final message → close → session log saved
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage


# ── ヘルパー ──────────────────────────────────────────────────────────────────

def make_session_graph(total_turns: int = 2):
    """指定ターン数の会話を行うグラフモック。最終ターンで done=True を返す。"""
    call_count = [0]
    mock_graph = MagicMock()

    async def mock_ainvoke(state):
        call_count[0] += 1
        done = call_count[0] >= total_turns
        return {
            "mental_state": "B",
            "mental_score": 0.65,
            "reasoning": "落ち着いた様子が見られます。",
            "score_breakdown": {
                "score": 0.65,
                "contributions": {"face": 0.23, "voice": 0.29, "text": 0.13},
                "weights": {"face": 0.35, "voice": 0.45, "text": 0.20},
            },
            "weights_used": {"face": 0.35, "voice": 0.45, "text": 0.20},
            "history": state["history"] + [AIMessage(content=f"ターン{call_count[0]}の質問")],
            "raw_metrics": {**state.get("raw_metrics", {}), "done": done},
        }

    mock_graph.ainvoke = mock_ainvoke
    return mock_graph


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# ── E2E: 完全セッションフロー ─────────────────────────────────────────────────

def test_e2e_full_session_single_turn(client):
    """E2E: 自己申告(pre) → センサー → 会話1ターン(done=True) → close"""
    with patch("app.routers.websocket.build_graph", return_value=make_session_graph(total_turns=1)), \
         patch("app.routers.websocket.save_session_log") as mock_save:

        with client.websocket_connect("/ws/e2e-session-001?subject_id=S001&consent_version=v1.0") as ws:
            # 1. 自己申告 (pre_session)
            ws.send_json({"type": "self_report", "timing": "pre_session", "score": 0.6})
            ack = ws.receive_json()
            assert ack["type"] == "ack"
            assert ack["timing"] == "pre_session"

            # 2. センサーデータ送信
            ws.send_json({
                "type": "face",
                "data": {"happy": 0.5, "angry": 0.1, "sad": 0.05, "neutral": 0.35, "stability": 0.8},
            })
            ws.send_json({
                "type": "text",
                "data": {"interval_ms": 110.0, "backspace_count": 1, "total_keys": 20,
                         "idle_ms": 300.0, "total_time_ms": 3000.0},
            })

            # 3. ユーザーメッセージ → グラフ実行 (done=True のため close が返る)
            ws.send_json({"type": "message", "data": {"text": "今日は少し疲れています", "input_mode": "text"}})
            state_resp = ws.receive_json()
            close_resp = ws.receive_json()

            assert state_resp["type"] == "state"
            assert state_resp["mental_state"] in {"A", "B", "C", "D-1", "D-2"}
            assert "score" in state_resp
            assert "reasoning" in state_resp
            assert close_resp["type"] == "close"

    # 切断後にセッションログが保存される
    mock_save.assert_called_once()
    call_kwargs = mock_save.call_args
    assert call_kwargs.kwargs.get("subject_id") == "S001"
    assert call_kwargs.kwargs.get("consent_version") == "v1.0"


def test_e2e_full_session_multi_turn(client):
    """E2E: 自己申告(pre) → 複数ターン → 自己申告(post) → 最終ターン → close"""
    with patch("app.routers.websocket.build_graph", return_value=make_session_graph(total_turns=2)), \
         patch("app.routers.websocket.save_session_log"):

        with client.websocket_connect("/ws/e2e-multi-turn") as ws:
            # 1. pre_session 自己申告
            ws.send_json({"type": "self_report", "timing": "pre_session", "score": 0.55})
            ack_pre = ws.receive_json()
            assert ack_pre["timing"] == "pre_session"

            # 2. ターン 1: done=False → question が返る
            ws.send_json({"type": "message", "data": {"text": "最近どうですか", "input_mode": "text"}})
            state1 = ws.receive_json()
            question1 = ws.receive_json()
            assert state1["type"] == "state"
            assert question1["type"] == "question"

            # 3. post_session 自己申告 (最終ターン前に送信)
            ws.send_json({"type": "self_report", "timing": "post_session", "score": 0.7})
            ack_post = ws.receive_json()
            assert ack_post["timing"] == "post_session"

            # 4. ターン 2: done=True → close が返る
            ws.send_json({"type": "message", "data": {"text": "少し疲れています", "input_mode": "text"}})
            state2 = ws.receive_json()
            close = ws.receive_json()
            assert state2["type"] == "state"
            assert close["type"] == "close"


def test_e2e_session_log_contains_required_fields(tmp_path):
    """E2E: セッションログが研究用フィールドを含む JSON として保存される"""
    from app.services.session_logger import save_session_log
    from langchain_core.messages import HumanMessage, AIMessage

    state = {
        "session_id": "e2e-log-test",
        "turn_count": 1,
        "mental_state": "B",
        "mental_score": 0.65,
        "score_breakdown": {
            "score": 0.65,
            "contributions": {"face": 0.23, "voice": 0.29, "text": 0.13},
            "weights": {"face": 0.35, "voice": 0.45, "text": 0.20},
        },
        "reasoning": "落ち着いた様子",
        "weights_used": {"face": 0.35, "voice": 0.45, "text": 0.20},
        "weight_mode": "fixed",
        "history": [
            HumanMessage(content="最近どうですか"),
            AIMessage(content="少し疲れています"),
        ],
        "raw_metrics": {"done": True},
        "self_report": {"pre_session": 0.6, "post_session": 0.7},
    }

    filepath = save_session_log(
        state, data_dir=tmp_path, subject_id="S001", consent_version="v1.0"
    )
    data = json.loads(filepath.read_text(encoding="utf-8"))

    # 研究用必須フィールド (Task 4.2 拡張)
    assert data["session_id"] == "e2e-log-test"
    assert data["subject_id"] == "S001"
    assert data["consent_version"] == "v1.0"
    assert data["weight_mode"] == "fixed"
    assert data["self_report"]["pre_session"] == pytest.approx(0.6)
    assert data["self_report"]["post_session"] == pytest.approx(0.7)
    assert len(data["turns"]) == 1
    assert data["turns"][0]["mental_state"] == "B"
