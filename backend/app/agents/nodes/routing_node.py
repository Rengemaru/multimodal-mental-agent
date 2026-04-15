"""Task 3.2.4: 分岐ロジックノード"""

from app.agents.state import AgentState

_CRISIS_STATES = {"D-1", "D-2"}


def routing_node(state: AgentState, max_turns: int = 10) -> str:
    """次に遷移するノード名を返す。

    'close' を返す条件:
      - turn_count >= max_turns (上限到達)
      - mental_state が D-1 または D-2 (危機状態)

    それ以外は 'question' を返す。
    """
    if state["turn_count"] >= max_turns:
        return "close"
    if state["mental_state"] in _CRISIS_STATES:
        return "close"
    return "question"
