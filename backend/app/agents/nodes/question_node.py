"""Task 3.2.1: 質問生成ノード"""

from langchain_core.messages import AIMessage

from app.agents.state import AgentState
from app.services.gemini import _generate_with_retry

_DIRECTION_MAP = {
    "A": "ポジティブな出来事や楽しいことについて深掘りする",
    "B": "日常の出来事や気持ちについて自然に聞く",
    "C": "悩みや気になっていることを優しく引き出す",
    "D-1": "何がストレスになっているかを穏やかに確認する",
    "D-2": "最近つらかったことを静かに聞く",
}


async def question_node(state: AgentState) -> dict:
    """メンタル状態に応じた質問を生成し、history に AIMessage として追加する。"""
    mental_state = state["mental_state"]
    direction = _DIRECTION_MAP.get(mental_state, _DIRECTION_MAP["B"])

    history_dicts = [
        {"question": msg.content, "answer": ""}
        if isinstance(msg, AIMessage)
        else {"question": "", "answer": msg.content}
        for msg in state["history"]
    ]

    history_text = "\n".join(
        f"AI: {t.get('question', '')}\nユーザー: {t.get('answer', '')}"
        for t in history_dicts[-3:]
    )

    prompt = f"""あなたはメンタル状況を把握するカウンセラーです。
非診断目的の研究用プロトタイプとして動作しています。

現在のメンタル状態: {mental_state}
質問の方向性: {direction}
これまでの会話:
{history_text if history_text else "（会話開始）"}

次の質問を1つだけ生成してください。
条件:
- 短く自然な日本語
- 答えを強迫しない
- クローズドクエスチョンを避ける
- 医療的アドバイスは含めない
質問のみ出力してください。"""

    question_text = await _generate_with_retry(prompt)
    new_message = AIMessage(content=question_text)

    return {
        "history": state["history"] + [new_message],
        "turn_count": state["turn_count"] + 1,
    }
