"""Task 4.1: WebSocket エンドポイント

イベントプロトコル (クライアント → サーバー):
  {"type": "face",        "data": FaceData}
  {"type": "voice",       "data": "<base64 WAV>"}
  {"type": "text",        "data": TextData}
  {"type": "self_report", "timing": "pre_session"|"post_session", "score": float}
  {"type": "message",     "data": {"text": str, "input_mode": "voice"|"text"}}

イベントプロトコル (サーバー → クライアント):
  {"type": "ack",      "timing": str}
  {"type": "state",    "mental_state": str, "score": float, "reasoning": str, "score_breakdown": dict}
  {"type": "question", "text": str}
  {"type": "close"}
"""

import base64

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.graph import build_graph
from app.agents.state import make_initial_state
from app.config import settings
from app.services.session_logger import save_session_log
from app.services.voice_analysis import analyze as analyze_voice

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    subject_id: str = "unknown",
    consent_version: str = "v1.0",
) -> None:
    await websocket.accept()

    graph = build_graph()
    state = make_initial_state(
        session_id=session_id,
        weight_mode=settings.weight_mode if hasattr(settings, "weight_mode") else "fixed",
    )

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            # ── センサーイベント: raw_metrics を更新 ──────────────────────────
            if event_type == "face":
                state["raw_metrics"]["face"] = data.get("data", {})

            elif event_type == "voice":
                raw_b64 = data.get("data", "")
                if raw_b64:
                    wav_bytes = base64.b64decode(raw_b64)
                    voice_data = analyze_voice(wav_bytes)
                    state["raw_metrics"]["voice"] = voice_data.model_dump()

            elif event_type == "text":
                state["raw_metrics"]["text"] = data.get("data", {})

            # ── 自己申告スコア ────────────────────────────────────────────────
            elif event_type == "self_report":
                timing = data.get("timing", "pre_session")
                score = float(data.get("score", 0.5))
                state["self_report"][timing] = score
                await websocket.send_json({"type": "ack", "timing": timing})

            # ── ユーザーメッセージ: グラフ実行 ────────────────────────────────
            elif event_type == "message":
                text = data.get("data", {}).get("text", "")
                state["history"] = state["history"] + [HumanMessage(content=text)]

                try:
                    result = await graph.ainvoke(state)
                    state.update(result)
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                    continue

                # state レスポンスを送信
                await websocket.send_json({
                    "type": "state",
                    "mental_state": state["mental_state"],
                    "score": state["mental_score"],
                    "reasoning": state["reasoning"],
                    "score_breakdown": state["score_breakdown"],
                })

                # AI の質問または終了を送信
                if state.get("raw_metrics", {}).get("done"):
                    await websocket.send_json({"type": "close"})
                    break
                else:
                    ai_msgs = [m for m in state["history"] if isinstance(m, AIMessage)]
                    if ai_msgs:
                        await websocket.send_json({
                            "type": "question",
                            "text": ai_msgs[-1].content,
                        })

    except WebSocketDisconnect:
        pass
    finally:
        save_session_log(
            state,
            data_dir="data/sessions",
            subject_id=subject_id,
            consent_version=consent_version,
        )
