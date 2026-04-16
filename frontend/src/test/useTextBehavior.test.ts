import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useTextBehavior } from "../hooks/useTextBehavior";

// ── ヘルパー ──────────────────────────────────────────────────────────────────

function makeKeyEvent(key: string): React.KeyboardEvent {
  return { key } as React.KeyboardEvent;
}

// ── 初期状態 ──────────────────────────────────────────────────────────────────

describe("useTextBehavior — 初期状態", () => {
  it("全メトリクスが 0 で初期化される", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));
    const { metrics } = result.current;
    expect(metrics.total_keys).toBe(0);
    expect(metrics.backspace_count).toBe(0);
    expect(metrics.interval_ms).toBe(0);
    expect(metrics.idle_ms).toBe(0);
    expect(metrics.total_time_ms).toBe(0);
  });
});

// ── handleKeyDown ─────────────────────────────────────────────────────────────

describe("useTextBehavior — handleKeyDown", () => {
  beforeEach(() => { vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); });

  it("キー入力で total_keys が増加する", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => { result.current.handleKeyDown(makeKeyEvent("b")); });

    expect(result.current.metrics.total_keys).toBe(2);
  });

  it("Backspace で backspace_count が増加する", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => { result.current.handleKeyDown(makeKeyEvent("Backspace")); });
    act(() => { result.current.handleKeyDown(makeKeyEvent("Backspace")); });

    expect(result.current.metrics.backspace_count).toBe(2);
    expect(result.current.metrics.total_keys).toBe(3);
  });

  it("2回目以降のキー入力で interval_ms が計算される", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => {
      vi.advanceTimersByTime(200);
      result.current.handleKeyDown(makeKeyEvent("b"));
    });
    act(() => {
      vi.advanceTimersByTime(200);
      result.current.handleKeyDown(makeKeyEvent("c"));
    });

    // 平均インターバル = 200ms
    expect(result.current.metrics.interval_ms).toBeCloseTo(200, 0);
  });

  it("長い無入力時間が idle_ms に加算される", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => {
      vi.advanceTimersByTime(3000); // 3秒の無入力
      result.current.handleKeyDown(makeKeyEvent("b"));
    });

    expect(result.current.metrics.idle_ms).toBeGreaterThan(0);
  });

  it("短い入力間隔は idle_ms に加算されない", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => {
      vi.advanceTimersByTime(500); // 0.5秒 (閾値以下)
      result.current.handleKeyDown(makeKeyEvent("b"));
    });

    expect(result.current.metrics.idle_ms).toBe(0);
  });

  it("total_time_ms は最初のキーからの経過時間", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => {
      vi.advanceTimersByTime(1000);
      result.current.handleKeyDown(makeKeyEvent("b"));
    });

    expect(result.current.metrics.total_time_ms).toBeCloseTo(1000, -2);
  });
});

// ── sendMetrics ───────────────────────────────────────────────────────────────

describe("useTextBehavior — sendMetrics", () => {
  it("text イベントを送信する", () => {
    const sendJson = vi.fn();
    const { result } = renderHook(() => useTextBehavior(sendJson));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => { result.current.sendMetrics("こんにちは"); });

    const textCall = sendJson.mock.calls.find(
      (c) => (c[0] as { type: string }).type === "text"
    );
    expect(textCall).toBeDefined();
    const payload = textCall![0] as { type: string; data: Record<string, unknown> };
    expect(payload.data).toHaveProperty("total_keys");
    expect(payload.data).toHaveProperty("backspace_count");
    expect(payload.data).toHaveProperty("interval_ms");
    expect(payload.data).toHaveProperty("idle_ms");
    expect(payload.data).toHaveProperty("total_time_ms");
  });

  it("message イベントをテキストと input_mode: text で送信する", () => {
    const sendJson = vi.fn();
    const { result } = renderHook(() => useTextBehavior(sendJson));

    act(() => { result.current.sendMetrics("こんにちは"); });

    const msgCall = sendJson.mock.calls.find(
      (c) => (c[0] as { type: string }).type === "message"
    );
    expect(msgCall).toBeDefined();
    const payload = msgCall![0] as { type: string; data: { text: string; input_mode: string } };
    expect(payload.data.text).toBe("こんにちは");
    expect(payload.data.input_mode).toBe("text");
  });

  it("sendMetrics 後にメトリクスがリセットされる", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => { result.current.handleKeyDown(makeKeyEvent("b")); });
    act(() => { result.current.sendMetrics("ab"); });

    expect(result.current.metrics.total_keys).toBe(0);
    expect(result.current.metrics.backspace_count).toBe(0);
  });
});

// ── resetMetrics ──────────────────────────────────────────────────────────────

describe("useTextBehavior — resetMetrics", () => {
  it("全メトリクスを 0 に戻す", () => {
    const { result } = renderHook(() => useTextBehavior(vi.fn()));

    act(() => { result.current.handleKeyDown(makeKeyEvent("a")); });
    act(() => { result.current.handleKeyDown(makeKeyEvent("Backspace")); });
    act(() => { result.current.resetMetrics(); });

    const { metrics } = result.current;
    expect(metrics.total_keys).toBe(0);
    expect(metrics.backspace_count).toBe(0);
    expect(metrics.interval_ms).toBe(0);
  });
});
