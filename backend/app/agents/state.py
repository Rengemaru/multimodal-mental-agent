from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    session_id: str
    turn_count: int
    mental_state: str                    # "A" | "B" | "C" | "D-1" | "D-2"
    mental_score: float                  # 0.0 – 1.0
    score_breakdown: dict                # 改善案② 寄与度・重みを含む内訳
    reasoning: str                       # 改善案③ 自然言語の推定理由
    weights_used: dict                   # 改善案④ 実際に使用した重み
    weight_mode: Literal["fixed", "dynamic", "learned"]
    history: list[BaseMessage]           # LangChain メッセージ履歴
    raw_metrics: dict                    # 各ターンの生メトリクス
    self_report: dict                    # 改善案② 自己申告スコア


def make_initial_state(
    session_id: str,
    weight_mode: Literal["fixed", "dynamic", "learned"] = "fixed",
) -> AgentState:
    """セッション開始時の初期 AgentState を生成する。"""
    return AgentState(
        session_id=session_id,
        turn_count=0,
        mental_state="B",
        mental_score=0.5,
        score_breakdown={},
        reasoning="",
        weights_used={},
        weight_mode=weight_mode,
        history=[],
        raw_metrics={},
        self_report={},
    )
