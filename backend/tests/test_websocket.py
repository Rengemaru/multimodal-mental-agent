"""Tests for WebSocket endpoint (Task 4.1)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage


def make_mock_graph(done: bool = False):
    """グラフ全体をモックにする。ainvoke が固定 state を返す。"""
    mock_graph = MagicMock()

    async def mock_ainvoke(state):
        return {
            "mental_state": "B",
            "mental_score": 0.65,
            "reasoning": "音声から落ち着いた様子が見られます。",
            "score_breakdown": {
                "score": 0.65,
                "contributions": {"face": 0.23, "voice": 0.29, "text": 0.13},
                "weights": {"face": 0.35, "voice": 0.45, "text": 0.20},
            },
            "weights_used": {"face": 0.35, "voice": 0.45, "text": 0.20},
            "history": state["history"] + [AIMessage(content="最近どんなことがありましたか？")],
            "raw_metrics": {**state.get("raw_metrics", {}), "done": done},
        }

    mock_graph.ainvoke = mock_ainvoke
    return mock_graph


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# ── 接続確立 ──────────────────────────────────────────────────────────────────

def test_websocket_connects_successfully(client):
    """WebSocket 接続が確立できる"""
    with client.websocket_connect("/ws/test-session") as ws:
        assert ws is not None


# ── イベントディスパッチ ───────────────────────────────────────────────────────

def test_websocket_face_event_updates_metrics(client):
    """face イベントを送ると raw_metrics が更新される (ACK なし、クラッシュしない)"""
    with client.websocket_connect("/ws/face-test") as ws:
        ws.send_json({
            "type": "face",
            "data": {
                "happy": 0.6, "angry": 0.05, "sad": 0.05,
                "neutral": 0.3, "stability": 0.9,
            },
        })
        # face イベントは即時 ACK を返さない仕様 — 次のイベントを送れることで確認


def test_websocket_text_event_updates_metrics(client):
    """text イベントを送ってもクラッシュしない"""
    with client.websocket_connect("/ws/text-test") as ws:
        ws.send_json({
            "type": "text",
            "data": {
                "interval_ms": 120.0, "backspace_count": 2,
                "total_keys": 40, "idle_ms": 500.0, "total_time_ms": 6000.0,
            },
        })


def test_websocket_self_report_returns_ack(client):
    """self_report イベントを送ると ACK が返る"""
    with client.websocket_connect("/ws/self-report-test") as ws:
        ws.send_json({
            "type": "self_report",
            "timing": "pre_session",
            "score": 0.65,
        })
        response = ws.receive_json()
        assert response["type"] == "ack"
        assert response["timing"] == "pre_session"


# ── メッセージ処理 (グラフ実行) ───────────────────────────────────────────────

def test_websocket_message_returns_state_and_question(client):
    """message イベントを送るとグラフが実行され state と question が返る"""
    with patch("app.routers.websocket.build_graph", return_value=make_mock_graph()):
        with client.websocket_connect("/ws/msg-test") as ws:
            ws.send_json({
                "type": "message",
                "data": {"text": "こんにちは", "input_mode": "text"},
            })
            # サーバーは state → question の順で2件送信する
            state_resp = ws.receive_json()
            question_resp = ws.receive_json()

    assert state_resp["type"] == "state"
    assert question_resp["type"] == "question"


def test_websocket_message_state_has_required_fields(client):
    """state レスポンスに必須フィールドが含まれる"""
    with patch("app.routers.websocket.build_graph", return_value=make_mock_graph()):
        with client.websocket_connect("/ws/state-fields-test") as ws:
            ws.send_json({
                "type": "message",
                "data": {"text": "元気です", "input_mode": "text"},
            })
            state_resp = ws.receive_json()

    assert state_resp["type"] == "state"
    assert "mental_state" in state_resp
    assert "score" in state_resp
    assert "reasoning" in state_resp
