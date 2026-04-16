/**
 * Task 6.3: テキスト入力行動解析フック
 *
 * キーストロークのタイミングを追跡し、送信時にメトリクスを
 * WebSocket の text イベント + message イベントとして送信する。
 */

import { useCallback, useRef, useState } from "react";

/** 無入力とみなす閾値 (ms) */
const IDLE_THRESHOLD_MS = 2000;

export interface TextBehaviorMetrics {
  interval_ms: number;    // キー間の平均インターバル
  backspace_count: number; // バックスペース回数
  total_keys: number;     // 総キー入力数
  idle_ms: number;        // 無入力の合計時間
  total_time_ms: number;  // 最初のキーからの経過時間
}

const INITIAL_METRICS: TextBehaviorMetrics = {
  interval_ms: 0,
  backspace_count: 0,
  total_keys: 0,
  idle_ms: 0,
  total_time_ms: 0,
};

export interface UseTextBehaviorReturn {
  metrics: TextBehaviorMetrics;
  handleKeyDown: (event: React.KeyboardEvent) => void;
  sendMetrics: (text: string) => void;
  resetMetrics: () => void;
}

export function useTextBehavior(sendJson: (data: object) => void): UseTextBehaviorReturn {
  const [metrics, setMetrics] = useState<TextBehaviorMetrics>(INITIAL_METRICS);

  // 内部カウンタは ref で管理 (再レンダーを減らすため)
  const firstKeyTimeRef = useRef<number | null>(null);
  const lastKeyTimeRef = useRef<number | null>(null);
  const intervalSumRef = useRef(0);
  const intervalCountRef = useRef(0);
  const idleMsRef = useRef(0);
  const backspaceCountRef = useRef(0);
  const totalKeysRef = useRef(0);

  const sendJsonRef = useRef(sendJson);
  sendJsonRef.current = sendJson;

  const resetRefs = useCallback(() => {
    firstKeyTimeRef.current = null;
    lastKeyTimeRef.current = null;
    intervalSumRef.current = 0;
    intervalCountRef.current = 0;
    idleMsRef.current = 0;
    backspaceCountRef.current = 0;
    totalKeysRef.current = 0;
  }, []);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    const now = Date.now();

    if (firstKeyTimeRef.current === null) {
      firstKeyTimeRef.current = now;
    }

    if (lastKeyTimeRef.current !== null) {
      const gap = now - lastKeyTimeRef.current;
      intervalSumRef.current += gap;
      intervalCountRef.current += 1;
      if (gap >= IDLE_THRESHOLD_MS) {
        idleMsRef.current += gap;
      }
    }

    lastKeyTimeRef.current = now;
    totalKeysRef.current += 1;

    if (event.key === "Backspace") {
      backspaceCountRef.current += 1;
    }

    const elapsed = now - (firstKeyTimeRef.current ?? now);
    setMetrics({
      interval_ms:
        intervalCountRef.current > 0
          ? intervalSumRef.current / intervalCountRef.current
          : 0,
      backspace_count: backspaceCountRef.current,
      total_keys: totalKeysRef.current,
      idle_ms: idleMsRef.current,
      total_time_ms: elapsed,
    });
  }, []);

  const sendMetrics = useCallback(
    (text: string) => {
      const now = Date.now();
      const totalTimeMs =
        firstKeyTimeRef.current !== null ? now - firstKeyTimeRef.current : 0;

      const textData: TextBehaviorMetrics = {
        interval_ms:
          intervalCountRef.current > 0
            ? intervalSumRef.current / intervalCountRef.current
            : 0,
        backspace_count: backspaceCountRef.current,
        total_keys: totalKeysRef.current,
        idle_ms: idleMsRef.current,
        total_time_ms: totalTimeMs,
      };

      sendJsonRef.current({ type: "text", data: textData });
      sendJsonRef.current({
        type: "message",
        data: { text, input_mode: "text" },
      });

      resetRefs();
      setMetrics(INITIAL_METRICS);
    },
    [resetRefs],
  );

  const resetMetrics = useCallback(() => {
    resetRefs();
    setMetrics(INITIAL_METRICS);
  }, [resetRefs]);

  return { metrics, handleKeyDown, sendMetrics, resetMetrics };
}
