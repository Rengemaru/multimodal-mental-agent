from app.models.metrics import FaceData, TextData, VoiceData

WEIGHTS_DEFAULT: dict[str, float] = {"face": 0.35, "voice": 0.45, "text": 0.20}


def compute_dynamic_weights(
    face_quality: float, voice_quality: float, text_quality: float
) -> dict[str, float]:
    """信頼度ベースの動的重み計算 (改善案④)。
    各モダリティの品質スコア(0~1)を正規化して重みとして返す。
    全ゼロの場合は均等分配にフォールバック。
    """
    confidence = {"face": face_quality, "voice": voice_quality, "text": text_quality}
    total = sum(confidence.values())
    if total == 0.0:
        n = len(confidence)
        return {k: 1.0 / n for k in confidence}
    return {k: v / total for k, v in confidence.items()}


def compute_mental_score(
    face_score: float,
    voice_score: float,
    text_score: float,
    weights: dict[str, float],
) -> dict:
    """各モダリティの寄与度と総合スコアを返す。

    Returns:
        {
            "score": float,           # 総合スコア 0.0–1.0
            "contributions": dict,    # モダリティ別寄与度
            "weights": dict,          # 使用した重み
        }
    """
    contributions = {
        "face": face_score * weights["face"],
        "voice": voice_score * weights["voice"],
        "text": text_score * weights["text"],
    }
    return {
        "score": sum(contributions.values()),
        "contributions": contributions,
        "weights": weights,
    }


def classify_state(
    score: float, face: FaceData, voice: VoiceData, text: TextData
) -> str:
    """メンタル状態を A / B / C / D-1 / D-2 に分類する。

    A: score >= 0.75  (良好)
    B: score >= 0.50  (やや良好)
    C: score >= 0.25  (要注意)
    D-1: score < 0.25 かつ 怒りシグナル優位
    D-2: score < 0.25 かつ 悲しみシグナル優位 (改善案⑥)
    """
    if score >= 0.75:
        return "A"
    if score >= 0.50:
        return "B"
    if score >= 0.25:
        return "C"

    # D-1 / D-2 判定: 表情・音声・テキストを統合したシグナル計算
    anger_signal = (
        face.angry * 0.5
        + (1.0 if voice.rms_std > 0.3 else 0.0) * 0.3
        + (1.0 if voice.speech_rate > 5.0 else 0.0) * 0.2
    )
    sad_signal = (
        face.sad * 0.5
        + (1.0 if voice.rms_mean < 0.2 else 0.0) * 0.3
        + (1.0 if text.idle_ms > 3000 else 0.0) * 0.2
    )
    return "D-1" if anger_signal > sad_signal else "D-2"
