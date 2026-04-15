"""Tests for Gemini API client (Task 2.1) — uses mocks for external API.

Integration tests (marked with @pytest.mark.integration) require a real
GEMINI_API_KEY and are excluded from CI.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── generate_question ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_question_returns_string():
    """generate_question が文字列を返す"""
    mock_response = MagicMock()
    mock_response.text = "最近、気になっていることはありますか？"

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        from app.services.gemini import generate_question
        result = await generate_question(
            mental_state="B",
            history=[],
            direction="日常の出来事について聞く",
        )
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_question_calls_gemini_api():
    """generate_question が Gemini API を1回呼び出す"""
    mock_response = MagicMock()
    mock_response.text = "今日はどんな一日でしたか？"

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        from app.services.gemini import generate_question
        await generate_question(mental_state="A", history=[], direction="ポジティブな話題")
        mock_client.aio.models.generate_content.assert_called_once()


# ── generate_reasoning ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_reasoning_returns_string():
    """generate_reasoning がスコア内訳から文字列の理由を返す"""
    mock_response = MagicMock()
    mock_response.text = "表情からは落ち着いた様子が見られます。"

    score_breakdown = {
        "score": 0.65,
        "contributions": {"face": 0.28, "voice": 0.27, "text": 0.10},
        "weights": {"face": 0.35, "voice": 0.45, "text": 0.20},
    }

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        from app.services.gemini import generate_reasoning
        result = await generate_reasoning(score_breakdown=score_breakdown)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_reasoning_calls_gemini_api():
    """generate_reasoning が Gemini API を1回呼び出す"""
    mock_response = MagicMock()
    mock_response.text = "音声から緊張が感じられます。"

    with patch("app.services.gemini.client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        from app.services.gemini import generate_reasoning
        await generate_reasoning(score_breakdown={"score": 0.3, "contributions": {}, "weights": {}})
        mock_client.aio.models.generate_content.assert_called_once()


# ── リトライロジック ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retries_on_transient_error():
    """一時的なエラーが発生した場合にリトライして成功する"""
    mock_response = MagicMock()
    mock_response.text = "こんにちは"

    call_count = 0

    async def flaky_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("transient error")
        return mock_response

    with patch("app.services.gemini.client") as mock_client:
        with patch("app.services.gemini.asyncio.sleep", new_callable=AsyncMock):
            mock_client.aio.models.generate_content = flaky_generate
            from app.services.gemini import generate_question
            result = await generate_question(mental_state="B", history=[], direction="test")
    assert result == "こんにちは"
    assert call_count == 2


@pytest.mark.asyncio
async def test_raises_after_max_retries():
    """MAX_RETRIES 回失敗したら例外を送出する"""
    with patch("app.services.gemini.client") as mock_client:
        with patch("app.services.gemini.asyncio.sleep", new_callable=AsyncMock):
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=Exception("persistent error")
            )
            from app.services.gemini import generate_question
            with pytest.raises(Exception, match="persistent error"):
                await generate_question(mental_state="D-1", history=[], direction="test")
