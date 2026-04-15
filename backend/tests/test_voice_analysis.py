"""Tests for voice analysis service (Task 2.3).

実際の librosa を使用するが外部 API には依存しない。
テスト用音声は numpy で生成したサイン波・無音 WAV を使う。
"""

import io
import math
import wave

import numpy as np
import pytest

from app.models.metrics import VoiceData


# ── テスト用 WAV 生成ヘルパー ─────────────────────────────────────────────────

def make_sine_wav(frequency: float = 220.0, duration: float = 1.0, sample_rate: int = 22050) -> bytes:
    """サイン波の WAV バイナリを生成する。"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    samples = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


def make_silent_wav(duration: float = 1.0, sample_rate: int = 22050) -> bytes:
    """無音の WAV バイナリを生成する。"""
    samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


# ── 正常系 ────────────────────────────────────────────────────────────────────

def test_analyze_returns_voice_data():
    """WAV バイナリを渡すと VoiceData が返る"""
    from app.services.voice_analysis import analyze
    result = analyze(make_sine_wav())
    assert isinstance(result, VoiceData)


def test_analyze_all_fields_are_finite():
    """全フィールドが有限値 (NaN / inf でない)"""
    from app.services.voice_analysis import analyze
    result = analyze(make_sine_wav())
    for field, value in result.model_dump().items():
        assert math.isfinite(value), f"{field} is not finite: {value}"


def test_analyze_rms_positive_for_audio():
    """音声ありの場合、rms_mean > 0"""
    from app.services.voice_analysis import analyze
    result = analyze(make_sine_wav(frequency=220.0, duration=1.0))
    assert result.rms_mean > 0.0


def test_analyze_speech_rate_non_negative():
    """話速は非負"""
    from app.services.voice_analysis import analyze
    result = analyze(make_sine_wav())
    assert result.speech_rate >= 0.0


def test_analyze_silence_duration_non_negative():
    """沈黙時間は非負"""
    from app.services.voice_analysis import analyze
    result = analyze(make_sine_wav())
    assert result.silence_duration >= 0.0


# ── 無音入力 ──────────────────────────────────────────────────────────────────

def test_analyze_silent_audio_does_not_crash():
    """無音入力でもクラッシュしない"""
    from app.services.voice_analysis import analyze
    result = analyze(make_silent_wav())
    assert isinstance(result, VoiceData)


def test_analyze_silent_audio_has_low_rms():
    """無音の rms_mean はほぼ 0"""
    from app.services.voice_analysis import analyze
    result = analyze(make_silent_wav())
    assert result.rms_mean < 0.01


def test_analyze_silent_audio_all_fields_are_finite():
    """無音でも全フィールドが有限値"""
    from app.services.voice_analysis import analyze
    result = analyze(make_silent_wav())
    for field, value in result.model_dump().items():
        assert math.isfinite(value), f"{field} is not finite: {value}"
