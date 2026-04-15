"""Task 3.2.3: 理由生成ノード (改善案③)"""

from app.agents.state import AgentState
from app.services.gemini import _generate_with_retry


async def reasoning_node(state: AgentState) -> dict:
    """score_breakdown から自然言語の推定理由を生成する。"""
    breakdown = state.get("score_breakdown", {})
    contributions = breakdown.get("contributions", {})
    weights = breakdown.get("weights", {})
    total_score = breakdown.get("score", state.get("mental_score", 0.5))

    prompt = f"""あなたはメンタル状況分析AIです。
以下のマルチモーダル分析結果から、メンタル状態の推定理由を自然な日本語で説明してください。

総合スコア: {total_score:.2f}
モダリティ別寄与度:
  - 表情: {contributions.get('face', 0.0):.2f} (重み {weights.get('face', 0.0):.2f})
  - 音声: {contributions.get('voice', 0.0):.2f} (重み {weights.get('voice', 0.0):.2f})
  - テキスト: {contributions.get('text', 0.0):.2f} (重み {weights.get('text', 0.0):.2f})

条件:
- 2〜3文で簡潔に
- 断定的な表現を避ける（「〜が見られます」「〜と考えられます」など）
- 医療的診断は含めない
説明のみ出力してください。"""

    reasoning = await _generate_with_retry(prompt)
    return {"reasoning": reasoning}
