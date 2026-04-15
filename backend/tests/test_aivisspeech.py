"""Tests for AivisSpeech TTS client (Task 2.2).

AivisSpeech は VOICEVOX 互換 API:
  POST /audio_query?text=...&speaker=... → audio query JSON
  POST /synthesis?speaker=...  body=audio_query → WAV bytes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


# ── 正常系 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_synthesize_returns_bytes():
    """正常系: WAV バイナリ (bytes) が返る"""
    fake_wav = b"RIFF\x00\x00\x00\x00WAVEfmt "

    mock_query_resp = MagicMock()
    mock_query_resp.json.return_value = {"speedScale": 1.0}
    mock_query_resp.raise_for_status = MagicMock()

    mock_synth_resp = MagicMock()
    mock_synth_resp.content = fake_wav
    mock_synth_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[mock_query_resp, mock_synth_resp])

    with patch("app.services.aivisspeech.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.aivisspeech import synthesize
        result = await synthesize("こんにちは")

    assert isinstance(result, bytes)
    assert result == fake_wav


@pytest.mark.asyncio
async def test_synthesize_calls_audio_query_then_synthesis():
    """audio_query → synthesis の順で2回 POST が呼ばれる"""
    fake_query = {"speedScale": 1.0, "pitchScale": 0.0}
    fake_wav = b"RIFF"

    mock_query_resp = MagicMock()
    mock_query_resp.json.return_value = fake_query
    mock_query_resp.raise_for_status = MagicMock()

    mock_synth_resp = MagicMock()
    mock_synth_resp.content = fake_wav
    mock_synth_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[mock_query_resp, mock_synth_resp])

    with patch("app.services.aivisspeech.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.aivisspeech import synthesize
        await synthesize("テスト")

    assert mock_client.post.call_count == 2
    first_call_url = mock_client.post.call_args_list[0][0][0]
    second_call_url = mock_client.post.call_args_list[1][0][0]
    assert "audio_query" in first_call_url
    assert "synthesis" in second_call_url


# ── フォールバック ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_synthesize_returns_none_when_server_down():
    """AivisSpeech が落ちている場合は None を返す (エラーにしない)"""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    with patch("app.services.aivisspeech.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.aivisspeech import synthesize
        result = await synthesize("こんにちは")

    assert result is None


@pytest.mark.asyncio
async def test_synthesize_returns_none_on_http_error():
    """HTTP エラー (4xx/5xx) でも None を返す"""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock()
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.aivisspeech.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.aivisspeech import synthesize
        result = await synthesize("こんにちは")

    assert result is None


@pytest.mark.asyncio
async def test_synthesize_returns_none_on_timeout():
    """タイムアウト時も None を返す"""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("app.services.aivisspeech.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.services.aivisspeech import synthesize
        result = await synthesize("こんにちは")

    assert result is None
