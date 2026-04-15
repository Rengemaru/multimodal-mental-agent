"""Task 3.2.5: 終了処理ノード"""

from app.agents.state import AgentState


async def close_node(state: AgentState) -> dict:
    """セッションを終了し、raw_metrics に done フラグを立てる。"""
    updated_metrics = {**state.get("raw_metrics", {}), "done": True}
    return {"raw_metrics": updated_metrics}
