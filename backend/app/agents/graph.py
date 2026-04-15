"""Task 3.3: LangGraph StateGraph 構築

グラフの流れ (1ターンあたり):
  START
    → analysis    : raw_metrics からメンタル状態を推定
    → reasoning   : スコア内訳から自然言語の理由を生成 (改善案③)
    → [routing]   : turn_count / mental_state で分岐
        ├─ "question" → question : 次の質問を生成して END (次ターンを待つ)
        └─ "close"   → close    : セッション終了フラグを立てて END
"""

from functools import partial

from langgraph.graph import END, StateGraph

from app.agents.nodes.analysis_node import analysis_node
from app.agents.nodes.close_node import close_node
from app.agents.nodes.question_node import question_node
from app.agents.nodes.reasoning_node import reasoning_node
from app.agents.nodes.routing_node import routing_node
from app.agents.state import AgentState
from app.config import settings


def build_graph():
    """コンパイル済み LangGraph を返す。"""
    graph = StateGraph(AgentState)

    # ── ノード登録 ─────────────────────────────────────────────────────────────
    graph.add_node("analysis", analysis_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("question", question_node)
    graph.add_node("close", close_node)

    # ── エントリポイントとエッジ ──────────────────────────────────────────────
    graph.set_entry_point("analysis")
    graph.add_edge("analysis", "reasoning")

    # reasoning の後、routing_node の戻り値で条件分岐
    graph.add_conditional_edges(
        "reasoning",
        partial(routing_node, max_turns=settings.max_turns),
        {"question": "question", "close": "close"},
    )

    graph.add_edge("question", END)
    graph.add_edge("close", END)

    return graph.compile()
