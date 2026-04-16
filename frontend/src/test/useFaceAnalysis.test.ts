import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { expressionsToFaceData } from "../hooks/useFaceAnalysis";

// face-api.js を丸ごとモック (TensorFlow.js を jsdom で動かさないため)
vi.mock("face-api.js", () => ({
  nets: {
    tinyFaceDetector: { loadFromUri: vi.fn().mockResolvedValue(undefined) },
    faceExpressionNet: { loadFromUri: vi.fn().mockResolvedValue(undefined) },
  },
  TinyFaceDetectorOptions: vi.fn().mockImplementation(() => ({})),
  detectSingleFace: vi.fn().mockReturnValue({
    withFaceExpressions: vi.fn().mockResolvedValue(null),
  }),
}));

// ── ヘルパー ──────────────────────────────────────────────────────────────────

function makeExpressions(overrides: Record<string, number> = {}) {
  return {
    happy: 0.0,
    angry: 0.0,
    sad: 0.0,
    neutral: 1.0,
    surprised: 0.0,
    fearful: 0.0,
    disgusted: 0.0,
    ...overrides,
  };
}

function setupDeniedCamera() {
  Object.defineProperty(globalThis.navigator, "mediaDevices", {
    value: {
      getUserMedia: vi.fn().mockRejectedValue(new Error("Permission denied")),
    },
    writable: true,
    configurable: true,
  });
}

// Promise チェーンを複数段階フラッシュするヘルパー
async function flushPromises() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

// ── expressionsToFaceData (純粋関数) ──────────────────────────────────────────

describe("expressionsToFaceData", () => {
  it("表情スコアを FaceData にマッピングする", () => {
    const data = expressionsToFaceData(makeExpressions({ happy: 0.9, neutral: 0.1 }), []);
    expect(data.happy).toBeCloseTo(0.9);
    expect(data.neutral).toBeCloseTo(0.1);
    expect(data.angry).toBeCloseTo(0.0);
    expect(data.sad).toBeCloseTo(0.0);
  });

  it("stability が 0〜1 の範囲に収まる", () => {
    const data = expressionsToFaceData(makeExpressions(), []);
    expect(data.stability).toBeGreaterThanOrEqual(0);
    expect(data.stability).toBeLessThanOrEqual(1);
  });

  it("一定した履歴では stability が高い", () => {
    const history = [0.9, 0.9, 0.9, 0.9];
    const data = expressionsToFaceData(makeExpressions({ happy: 0.9, neutral: 0.1 }), history);
    expect(data.stability).toBeGreaterThan(0.7);
  });

  it("揺れている履歴では stability が低い", () => {
    const history = [0.0, 1.0, 0.0, 1.0];
    const data = expressionsToFaceData(makeExpressions({ happy: 0.5 }), history);
    expect(data.stability).toBeLessThan(0.5);
  });
});

// ── useFaceAnalysis — カメラ拒否フォールバック ────────────────────────────────

describe("useFaceAnalysis — カメラ拒否フォールバック", () => {
  beforeEach(() => {
    setupDeniedCamera();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("カメラ拒否時に cameraAllowed が false になる", async () => {
    const { useFaceAnalysis } = await import("../hooks/useFaceAnalysis");
    // 大きなインターバルを指定してフォールバック setInterval が干渉しないようにする
    const { result } = renderHook(() => useFaceAnalysis(vi.fn(), 60_000));

    await flushPromises();

    expect(result.current.cameraAllowed).toBe(false);
  });

  it("カメラ拒否時にフォールバックデータが定期送信される", async () => {
    const { useFaceAnalysis } = await import("../hooks/useFaceAnalysis");
    const onData = vi.fn();
    // 短いインターバルで実タイマーを使いデータ送信を確認
    renderHook(() => useFaceAnalysis(onData, 50));

    await flushPromises();

    // フォールバック setInterval が発火するまで待機
    await act(async () => {
      await new Promise((r) => setTimeout(r, 200));
    });

    expect(onData).toHaveBeenCalled();
    const arg = onData.mock.calls[0][0];
    expect(arg).toHaveProperty("happy");
    expect(arg).toHaveProperty("angry");
    expect(arg).toHaveProperty("sad");
    expect(arg).toHaveProperty("neutral");
    expect(arg).toHaveProperty("stability");
  });

  it("フォールバックデータのスコアはすべて 0〜1 に収まる", async () => {
    const { useFaceAnalysis } = await import("../hooks/useFaceAnalysis");
    const onData = vi.fn();
    renderHook(() => useFaceAnalysis(onData, 50));

    await flushPromises();
    await act(async () => {
      await new Promise((r) => setTimeout(r, 200));
    });

    if (onData.mock.calls.length > 0) {
      const arg = onData.mock.calls[0][0] as Record<string, number>;
      Object.values(arg).forEach((v) => {
        expect(v).toBeGreaterThanOrEqual(0);
        expect(v).toBeLessThanOrEqual(1);
      });
    }
  });
});
