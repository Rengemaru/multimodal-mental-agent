import asyncio

from google import genai

from app.config import settings

client = genai.Client(api_key=settings.gemini_api_key)

MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3


async def _generate_with_retry(prompt: str) -> str:
    """Gemini API を呼び出し、失敗時は指数バックオフでリトライする。"""
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.aio.models.generate_content(
                model=MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2**attempt)
    raise last_error  # type: ignore[misc]


async def generate_question(mental_state: str, history: list, direction: str) -> str:
    """メンタル状態と方向性に基づいて次の質問を生成する。"""
    history_text = "\n".join(
        f"AI: {turn.get('question', '')}\nユーザー: {turn.get('answer', '')}"
        for turn in history[-3:]  # 直近3ターンのみ参照
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
    return await _generate_with_retry(prompt)


async def generate_reasoning(score_breakdown: dict) -> str:
    """スコア内訳から自然言語の推定理由を生成する (改善案③)。"""
    contributions = score_breakdown.get("contributions", {})
    weights = score_breakdown.get("weights", {})
    total_score = score_breakdown.get("score", 0.0)

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
    return await _generate_with_retry(prompt)
