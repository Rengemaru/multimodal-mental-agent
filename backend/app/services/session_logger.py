"""Task 4.2: セッションログ保存サービス

セッション終了時に AgentState を JSON ファイルへ保存する。
保存先: data/sessions/{session_id}_{timestamp}.json
"""

from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from app.models.session import SessionLog, TurnLog


def build_turns(state: dict) -> list[TurnLog]:
    """history の HumanMessage / AIMessage ペアから TurnLog リストを構築する。"""
    history = state.get("history", [])
    turns: list[TurnLog] = []
    turn_num = 0
    i = 0

    while i < len(history):
        if isinstance(history[i], HumanMessage):
            answer = history[i].content
            question = ""
            if i + 1 < len(history) and isinstance(history[i + 1], AIMessage):
                question = history[i + 1].content
                i += 2
            else:
                i += 1
            turn_num += 1
            turns.append(
                TurnLog(
                    turn=turn_num,
                    question=question,
                    answer=answer,
                    mental_state=state.get("mental_state", ""),
                    mental_score=state.get("mental_score", 0.0),
                    score_breakdown=state.get("score_breakdown", {}),
                    metrics=state.get("raw_metrics", {}),
                )
            )
        else:
            i += 1

    return turns


def save_session_log(
    state: dict,
    data_dir: str | Path = "data/sessions",
    subject_id: str = "unknown",
    consent_version: str = "v1.0",
) -> Path:
    """AgentState をシリアライズして JSON ファイルに保存し、パスを返す。"""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_id = state.get("session_id", "unknown")
    filepath = data_dir / f"{session_id}_{timestamp}.json"

    log = SessionLog(
        session_id=session_id,
        subject_id=subject_id,
        consent_version=consent_version,
        self_report=state.get("self_report", {}),
        weights_used=state.get("weights_used", {}),
        weight_mode=state.get("weight_mode", "fixed"),
        turns=build_turns(state),
    )

    filepath.write_text(log.model_dump_json(indent=2), encoding="utf-8")
    return filepath
