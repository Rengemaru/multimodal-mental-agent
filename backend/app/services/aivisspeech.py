import httpx

from app.config import settings

_AUDIO_QUERY_TIMEOUT = 10.0
_SYNTHESIS_TIMEOUT = 30.0


async def synthesize(text: str) -> bytes | None:
    """テキストを AivisSpeech (VOICEVOX 互換 API) で WAV バイナリに変換する。

    AivisSpeech が起動していない場合や HTTP エラー時は None を返す。
    呼び出し元でフォールバック処理（テキストのみ返却など）を行うこと。

    手順:
      1. POST /audio_query  → 音声合成パラメータ JSON を取得
      2. POST /synthesis    → WAV バイナリを取得
    """
    speaker = settings.aivis_speaker_id
    base_url = settings.aivis_url

    try:
        async with httpx.AsyncClient() as client:
            # Step 1: audio_query
            query_resp = await client.post(
                f"{base_url}/audio_query",
                params={"text": text, "speaker": speaker},
                timeout=_AUDIO_QUERY_TIMEOUT,
            )
            query_resp.raise_for_status()
            audio_query = query_resp.json()

            # Step 2: synthesis
            synth_resp = await client.post(
                f"{base_url}/synthesis",
                params={"speaker": speaker},
                json=audio_query,
                timeout=_SYNTHESIS_TIMEOUT,
            )
            synth_resp.raise_for_status()
            return synth_resp.content

    except Exception:
        return None
