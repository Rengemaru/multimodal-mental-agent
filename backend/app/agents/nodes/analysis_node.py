"""Task 3.2.2: メンタル分析ノード"""

from app.agents.state import AgentState
from app.models.metrics import FaceData, TextData, VoiceData
from app.services.scoring import (
    WEIGHTS_DEFAULT,
    classify_state,
    compute_dynamic_weights,
    compute_mental_score,
)

_DEFAULT_FACE = FaceData(happy=0.4, angry=0.1, sad=0.1, neutral=0.4, stability=0.8)
_DEFAULT_VOICE = VoiceData(
    rms_mean=0.3, rms_std=0.05, pitch_mean=180.0,
    pitch_std=20.0, speech_rate=4.0, silence_duration=1.0,
)
_DEFAULT_TEXT = TextData(
    interval_ms=120.0, backspace_count=2,
    total_keys=40, idle_ms=500.0, total_time_ms=6000.0,
)


def _to_face(d: dict) -> FaceData:
    try:
        return FaceData(**d)
    except Exception:
        return _DEFAULT_FACE


def _to_voice(d: dict) -> VoiceData:
    try:
        return VoiceData(**d)
    except Exception:
        return _DEFAULT_VOICE


def _to_text(d: dict) -> TextData:
    try:
        return TextData(**d)
    except Exception:
        return _DEFAULT_TEXT


def _face_score(face: FaceData) -> float:
    """表情から 0–1 のスコアを算出する。"""
    return float(
        face.happy * 0.5
        + face.neutral * 0.3
        + (1.0 - face.angry) * 0.1
        + (1.0 - face.sad) * 0.1
    )


def _voice_score(voice: VoiceData) -> float:
    """音声特徴から 0–1 のスコアを算出する。"""
    calm = max(0.0, 1.0 - min(1.0, voice.rms_std / 0.5))
    pace = max(0.0, 1.0 - min(1.0, voice.speech_rate / 8.0))
    return float((calm + pace) / 2.0)


def _text_score(text: TextData) -> float:
    """テキスト行動から 0–1 のスコアを算出する。"""
    if text.total_keys == 0:
        return 0.5
    backspace_ratio = min(1.0, text.backspace_count / text.total_keys)
    return float(1.0 - backspace_ratio * 0.5)


async def analysis_node(state: AgentState) -> dict:
    """raw_metrics からスコアを算出し、メンタル状態を更新する。"""
    raw = state.get("raw_metrics", {})

    face = _to_face(raw.get("face", {}))
    voice = _to_voice(raw.get("voice", {}))
    text = _to_text(raw.get("text", {}))

    face_q = float(raw.get("face_quality", 1.0))
    voice_q = float(raw.get("voice_quality", 1.0))
    text_q = float(raw.get("text_quality", 1.0))

    weight_mode = state.get("weight_mode", "fixed")
    if weight_mode == "dynamic":
        weights = compute_dynamic_weights(face_q, voice_q, text_q)
    else:
        weights = WEIGHTS_DEFAULT

    fs = _face_score(face)
    vs = _voice_score(voice)
    ts = _text_score(text)

    breakdown = compute_mental_score(fs, vs, ts, weights)
    mental_state = classify_state(breakdown["score"], face, voice, text)

    return {
        "mental_state": mental_state,
        "mental_score": breakdown["score"],
        "score_breakdown": breakdown,
        "weights_used": weights,
    }
