from pydantic import BaseModel


class FaceData(BaseModel):
    happy: float
    angry: float
    sad: float
    neutral: float
    stability: float


class VoiceData(BaseModel):
    rms_mean: float
    rms_std: float
    pitch_mean: float
    pitch_std: float
    speech_rate: float
    silence_duration: float


class TextData(BaseModel):
    interval_ms: float
    backspace_count: int
    total_keys: int
    idle_ms: float
    total_time_ms: float
