import io

import librosa
import numpy as np

from app.models.metrics import VoiceData


def analyze(wav_bytes: bytes) -> VoiceData:
    """WAV バイナリから音声特徴量を抽出して VoiceData を返す。

    抽出する特徴量:
      - RMS (エネルギー): 平均・標準偏差
      - ピッチ (F0): 平均・標準偏差 (有声フレームのみ)
      - 話速: onset 数 / 秒
      - 沈黙時間: 無音区間の合計秒数
    """
    y, sr = librosa.load(io.BytesIO(wav_bytes), sr=None, mono=True)

    # ── RMS ──────────────────────────────────────────────────────────────────
    rms = librosa.feature.rms(y=y)[0]
    rms_mean = float(np.mean(rms))
    rms_std = float(np.std(rms))

    # ── ピッチ (YIN アルゴリズム) ─────────────────────────────────────────────
    # 無音・極短音声でも NaN/inf が出ないよう有声フレームのみ集計
    f0 = librosa.yin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr)
    voiced = f0[(f0 > 0) & np.isfinite(f0)]
    pitch_mean = float(np.mean(voiced)) if len(voiced) > 0 else 0.0
    pitch_std = float(np.std(voiced)) if len(voiced) > 0 else 0.0

    # ── 話速 (onset 数 / 秒) ──────────────────────────────────────────────────
    duration = len(y) / sr if sr > 0 else 1.0
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    speech_rate = float(len(onsets) / duration) if duration > 0 else 0.0

    # ── 沈黙時間 ──────────────────────────────────────────────────────────────
    intervals = librosa.effects.split(y, top_db=30)
    voiced_duration = sum((end - start) / sr for start, end in intervals)
    silence_duration = float(max(0.0, duration - voiced_duration))

    return VoiceData(
        rms_mean=rms_mean,
        rms_std=rms_std,
        pitch_mean=pitch_mean,
        pitch_std=pitch_std,
        speech_rate=speech_rate,
        silence_duration=silence_duration,
    )
