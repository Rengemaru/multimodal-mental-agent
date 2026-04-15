"""Tests for scoring service (Task 1.3) — RED phase.

Test cases specified in IMPLEMENTATION_GUIDE §5 Task 1.3:
  - test_fixed_weights_sum_to_one
  - test_dynamic_weights_sum_to_one
  - test_compute_mental_score_returns_breakdown
  - test_classify_state_boundary_075  (A判定)
  - test_classify_state_boundary_050  (B判定)
  - test_classify_state_boundary_025  (C判定)
  - test_classify_d1_when_anger_dominant
  - test_classify_d2_when_sadness_dominant
"""

import pytest
from app.models.metrics import FaceData, VoiceData, TextData


# ── ヘルパー: デフォルトのダミーデータ ───────────────────────────────────────

def make_face(happy=0.5, angry=0.1, sad=0.1, neutral=0.3, stability=0.8) -> FaceData:
    return FaceData(happy=happy, angry=angry, sad=sad, neutral=neutral, stability=stability)


def make_voice(rms_mean=0.3, rms_std=0.05, pitch_mean=180.0,
               pitch_std=20.0, speech_rate=4.0, silence_duration=1.0) -> VoiceData:
    return VoiceData(
        rms_mean=rms_mean, rms_std=rms_std,
        pitch_mean=pitch_mean, pitch_std=pitch_std,
        speech_rate=speech_rate, silence_duration=silence_duration,
    )


def make_text(interval_ms=120.0, backspace_count=2,
              total_keys=40, idle_ms=500.0, total_time_ms=6000.0) -> TextData:
    return TextData(
        interval_ms=interval_ms, backspace_count=backspace_count,
        total_keys=total_keys, idle_ms=idle_ms, total_time_ms=total_time_ms,
    )


# ── 重み計算 ──────────────────────────────────────────────────────────────────

def test_fixed_weights_sum_to_one():
    from app.services.scoring import WEIGHTS_DEFAULT
    total = sum(WEIGHTS_DEFAULT.values())
    assert abs(total - 1.0) < 1e-9


def test_dynamic_weights_sum_to_one():
    from app.services.scoring import compute_dynamic_weights
    weights = compute_dynamic_weights(face_quality=0.9, voice_quality=0.6, text_quality=0.3)
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_dynamic_weights_all_zero_does_not_crash():
    """全品質ゼロでも ZeroDivisionError にならない"""
    from app.services.scoring import compute_dynamic_weights
    weights = compute_dynamic_weights(face_quality=0.0, voice_quality=0.0, text_quality=0.0)
    assert abs(sum(weights.values()) - 1.0) < 1e-9


# ── スコア計算 ─────────────────────────────────────────────────────────────────

def test_compute_mental_score_returns_breakdown():
    from app.services.scoring import WEIGHTS_DEFAULT, compute_mental_score
    result = compute_mental_score(
        face_score=0.8, voice_score=0.6, text_score=0.7,
        weights=WEIGHTS_DEFAULT,
    )
    assert "score" in result
    assert "contributions" in result
    assert "weights" in result
    assert set(result["contributions"].keys()) == {"face", "voice", "text"}


def test_compute_mental_score_weighted_sum():
    from app.services.scoring import compute_mental_score
    weights = {"face": 0.5, "voice": 0.3, "text": 0.2}
    result = compute_mental_score(face_score=1.0, voice_score=0.0, text_score=0.0, weights=weights)
    assert abs(result["score"] - 0.5) < 1e-9


# ── 状態分類 ──────────────────────────────────────────────────────────────────

def test_classify_state_boundary_075():
    """score=0.75 → A"""
    from app.services.scoring import classify_state
    assert classify_state(0.75, make_face(), make_voice(), make_text()) == "A"


def test_classify_state_above_075():
    from app.services.scoring import classify_state
    assert classify_state(1.0, make_face(), make_voice(), make_text()) == "A"


def test_classify_state_boundary_050():
    """score=0.50 → B"""
    from app.services.scoring import classify_state
    assert classify_state(0.50, make_face(), make_voice(), make_text()) == "B"


def test_classify_state_just_below_075():
    """score=0.74 → B"""
    from app.services.scoring import classify_state
    assert classify_state(0.74, make_face(), make_voice(), make_text()) == "B"


def test_classify_state_boundary_025():
    """score=0.25 → C"""
    from app.services.scoring import classify_state
    assert classify_state(0.25, make_face(), make_voice(), make_text()) == "C"


def test_classify_state_just_below_050():
    """score=0.49 → C"""
    from app.services.scoring import classify_state
    assert classify_state(0.49, make_face(), make_voice(), make_text()) == "C"


def test_classify_d1_when_anger_dominant():
    """怒りシグナル優位 → D-1"""
    from app.services.scoring import classify_state
    face = make_face(angry=0.9, sad=0.0)          # anger_signal: 0.9*0.5=0.45
    voice = make_voice(rms_std=0.5, speech_rate=6.0)  # +0.3+0.2=0.95 total
    text = make_text(idle_ms=100.0)               # sad_signal 抑制
    assert classify_state(0.0, face, voice, text) == "D-1"


def test_classify_d2_when_sadness_dominant():
    """悲しみシグナル優位 → D-2"""
    from app.services.scoring import classify_state
    face = make_face(angry=0.0, sad=0.9)          # sad_signal: 0.9*0.5=0.45
    voice = make_voice(rms_mean=0.1, rms_std=0.05, speech_rate=2.0)  # +0.3
    text = make_text(idle_ms=5000.0)              # +0.2 → sad_signal=0.95
    assert classify_state(0.0, face, voice, text) == "D-2"
