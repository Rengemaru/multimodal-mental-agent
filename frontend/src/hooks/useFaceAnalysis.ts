/**
 * Task 6.1: face-api.js による表情解析フック
 *
 * モデルファイルは public/models/ に配置すること。
 * ダウンロード手順は README.md を参照。
 *
 * https://github.com/justadudewhohacks/face-api.js
 */

import { useEffect, useRef, useState } from "react";
import * as faceapi from "face-api.js";

const MODEL_URL = "/models";
const DEFAULT_INTERVAL_MS = 1000;
const HISTORY_SIZE = 5;

export interface FaceData {
  happy: number;
  angry: number;
  sad: number;
  neutral: number;
  stability: number;
}

export const FALLBACK_DATA: FaceData = {
  happy: 0.5,
  angry: 0.0,
  sad: 0.0,
  neutral: 0.5,
  stability: 0.5,
};

export interface UseFaceAnalysisReturn {
  isReady: boolean;
  cameraAllowed: boolean;
  videoRef: React.RefObject<HTMLVideoElement>;
}

/**
 * face-api.js の FaceExpressions を FaceData に変換する純粋関数。
 * stability は直近の支配的表情スコアの標準偏差から計算する。
 */
export function expressionsToFaceData(
  expressions: Record<string, number>,
  prevHistory: number[],
): FaceData {
  const { happy = 0, angry = 0, sad = 0, neutral = 0 } = expressions;
  const dominant = Math.max(happy, angry, sad, neutral);

  const history = [...prevHistory.slice(-(HISTORY_SIZE - 1)), dominant];
  const mean = history.reduce((s, v) => s + v, 0) / history.length;
  const variance = history.reduce((s, v) => s + (v - mean) ** 2, 0) / history.length;
  const stability = Math.max(0, Math.min(1, 1 - Math.sqrt(variance) * 4));

  return { happy, angry, sad, neutral, stability };
}

export function useFaceAnalysis(
  onData: (data: FaceData) => void,
  intervalMs: number = DEFAULT_INTERVAL_MS,
): UseFaceAnalysisReturn {
  const [isReady, setIsReady] = useState(false);
  const [cameraAllowed, setCameraAllowed] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const historyRef = useRef<number[]>([]);
  const onDataRef = useRef(onData);
  onDataRef.current = onData;

  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelled = false;

    async function init() {
      try {
        // モデルをロード
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]);

        // カメラを取得
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        if (!cancelled) setIsReady(true);

        // 定期検出
        intervalRef.current = setInterval(async () => {
          const video = videoRef.current;
          if (!video || video.readyState < 2) return;

          const detection = await faceapi
            .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
            .withFaceExpressions();

          if (detection && !cancelled) {
            const data = expressionsToFaceData(
              detection.expressions as unknown as Record<string, number>,
              historyRef.current,
            );
            const dominant = Math.max(data.happy, data.angry, data.sad, data.neutral);
            historyRef.current = [...historyRef.current.slice(-(HISTORY_SIZE - 1)), dominant];
            onDataRef.current(data);
          }
        }, intervalMs);
      } catch {
        // カメラ拒否 or モデルロード失敗 → フォールバック
        if (!cancelled) setCameraAllowed(false);
        intervalRef.current = setInterval(() => {
          if (!cancelled) onDataRef.current(FALLBACK_DATA);
        }, intervalMs);
      }
    }

    init();

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [intervalMs]);

  return { isReady, cameraAllowed, videoRef };
}
