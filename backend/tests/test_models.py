"""Tests for Pydantic data models (Task 1.2) — RED phase."""

import pytest
from pydantic import ValidationError


# ── metrics ──────────────────────────────────────────────────────────────────

class TestFaceData:
    def test_valid(self):
        from app.models.metrics import FaceData
        fd = FaceData(happy=0.8, angry=0.05, sad=0.05, neutral=0.1, stability=0.9)
        assert fd.happy == 0.8

    def test_missing_field_raises(self):
        from app.models.metrics import FaceData
        with pytest.raises(ValidationError):
            FaceData(happy=0.8)  # angry, sad, neutral, stability が欠けている

    def test_invalid_type_raises(self):
        from app.models.metrics import FaceData
        with pytest.raises(ValidationError):
            FaceData(happy="high", angry=0.0, sad=0.0, neutral=0.0, stability=0.0)


class TestVoiceData:
    def test_valid(self):
        from app.models.metrics import VoiceData
        vd = VoiceData(
            rms_mean=0.3, rms_std=0.05,
            pitch_mean=180.0, pitch_std=20.0,
            speech_rate=4.5, silence_duration=1.2,
        )
        assert vd.speech_rate == 4.5

    def test_missing_field_raises(self):
        from app.models.metrics import VoiceData
        with pytest.raises(ValidationError):
            VoiceData(rms_mean=0.3)


class TestTextData:
    def test_valid(self):
        from app.models.metrics import TextData
        td = TextData(
            interval_ms=120.0, backspace_count=3,
            total_keys=42, idle_ms=500.0, total_time_ms=8000.0,
        )
        assert td.backspace_count == 3

    def test_missing_field_raises(self):
        from app.models.metrics import TextData
        with pytest.raises(ValidationError):
            TextData(interval_ms=100.0)


# ── events ────────────────────────────────────────────────────────────────────

class TestUserMessage:
    def test_voice_mode(self):
        from app.models.events import UserMessage
        msg = UserMessage(text="こんにちは", input_mode="voice")
        assert msg.input_mode == "voice"

    def test_text_mode(self):
        from app.models.events import UserMessage
        msg = UserMessage(text="hello", input_mode="text")
        assert msg.input_mode == "text"

    def test_invalid_mode_raises(self):
        from app.models.events import UserMessage
        with pytest.raises(ValidationError):
            UserMessage(text="hello", input_mode="keyboard")


class TestSelfReportScore:
    def test_pre_session(self):
        from app.models.events import SelfReportScore
        s = SelfReportScore(timing="pre_session", score=0.6)
        assert s.score == 0.6

    def test_post_session(self):
        from app.models.events import SelfReportScore
        s = SelfReportScore(timing="post_session", score=0.8)
        assert s.timing == "post_session"

    def test_invalid_timing_raises(self):
        from app.models.events import SelfReportScore
        with pytest.raises(ValidationError):
            SelfReportScore(timing="mid_session", score=0.5)


class TestWebSocketEvents:
    def test_face_event_type_literal(self):
        from app.models.events import FaceEvent
        from app.models.metrics import FaceData
        ev = FaceEvent(data=FaceData(happy=0.5, angry=0.1, sad=0.1, neutral=0.3, stability=0.8))
        assert ev.type == "face"

    def test_voice_event_type_literal(self):
        from app.models.events import VoiceEvent
        from app.models.metrics import VoiceData
        ev = VoiceEvent(data=VoiceData(
            rms_mean=0.3, rms_std=0.05, pitch_mean=180.0,
            pitch_std=20.0, speech_rate=4.5, silence_duration=1.2,
        ))
        assert ev.type == "voice"

    def test_text_event_type_literal(self):
        from app.models.events import TextEvent
        from app.models.metrics import TextData
        ev = TextEvent(data=TextData(
            interval_ms=120.0, backspace_count=3,
            total_keys=42, idle_ms=500.0, total_time_ms=8000.0,
        ))
        assert ev.type == "text"


# ── session ───────────────────────────────────────────────────────────────────

class TestSessionLog:
    def test_valid_minimal(self):
        from app.models.session import SessionLog
        log = SessionLog(
            session_id="abc123",
            subject_id="S001",
            consent_version="v1.0",
            self_report={},
            weights_used={"face": 0.35, "voice": 0.45, "text": 0.20},
            weight_mode="fixed",
            turns=[],
        )
        assert log.session_id == "abc123"

    def test_weight_mode_values(self):
        from app.models.session import SessionLog
        for mode in ("fixed", "dynamic", "learned"):
            log = SessionLog(
                session_id="x",
                subject_id="S001",
                consent_version="v1.0",
                self_report={},
                weights_used={},
                weight_mode=mode,
                turns=[],
            )
            assert log.weight_mode == mode

    def test_invalid_weight_mode_raises(self):
        from app.models.session import SessionLog
        with pytest.raises(ValidationError):
            SessionLog(
                session_id="x",
                subject_id="S001",
                consent_version="v1.0",
                self_report={},
                weights_used={},
                weight_mode="unknown",
                turns=[],
            )
