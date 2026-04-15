from typing import Literal

from pydantic import BaseModel

from app.models.metrics import FaceData, TextData, VoiceData


class UserMessage(BaseModel):
    text: str
    input_mode: Literal["voice", "text"]


class SelfReportScore(BaseModel):
    timing: Literal["pre_session", "post_session"]
    score: float  # 0.0 - 1.0


class FaceEvent(BaseModel):
    type: Literal["face"] = "face"
    data: FaceData


class VoiceEvent(BaseModel):
    type: Literal["voice"] = "voice"
    data: VoiceData


class TextEvent(BaseModel):
    type: Literal["text"] = "text"
    data: TextData


class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    data: UserMessage
