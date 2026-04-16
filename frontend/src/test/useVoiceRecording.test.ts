import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useVoiceRecording } from "../hooks/useVoiceRecording";

// ── MockMediaRecorder ─────────────────────────────────────────────────────────

class MockMediaRecorder {
  static instances: MockMediaRecorder[] = [];
  static isTypeSupported = vi.fn().mockReturnValue(true);

  state: string = "inactive";
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: ((event: Event) => void) | null = null;

  constructor(_stream: MediaStream, _options?: MediaRecorderOptions) {
    MockMediaRecorder.instances.push(this);
  }

  start() {
    this.state = "recording";
  }

  stop() {
    this.state = "inactive";
    this.ondataavailable?.({ data: new Blob(["mock-audio"], { type: "audio/webm" }) });
    this.onstop?.(new Event("stop"));
  }
}

// ── セットアップ ───────────────────────────────────────────────────────────────

const mockTrackStop = vi.fn();
const mockStream = {
  getTracks: () => [{ stop: mockTrackStop }],
} as unknown as MediaStream;

function setupMocks(allowMic = true) {
  MockMediaRecorder.instances = [];
  vi.stubGlobal("MediaRecorder", MockMediaRecorder);
  Object.defineProperty(globalThis.navigator, "mediaDevices", {
    value: {
      getUserMedia: allowMic
        ? vi.fn().mockResolvedValue(mockStream)
        : vi.fn().mockRejectedValue(new Error("Permission denied")),
    },
    writable: true,
    configurable: true,
  });
}

async function flushAsync() {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 50));
  });
}

// ── テスト ────────────────────────────────────────────────────────────────────

describe("useVoiceRecording — 初期状態", () => {
  beforeEach(() => setupMocks());
  afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

  it("初期状態では isRecording が false", () => {
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));
    expect(result.current.isRecording).toBe(false);
  });

  it("初期状態では micAllowed が true", () => {
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));
    expect(result.current.micAllowed).toBe(true);
  });
});

describe("useVoiceRecording — 録音開始・停止", () => {
  beforeEach(() => setupMocks());
  afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

  it("startRecording 後に isRecording が true になる", async () => {
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isRecording).toBe(true);
  });

  it("stopRecording 後に isRecording が false になる", async () => {
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));

    await act(async () => {
      await result.current.startRecording();
    });
    act(() => {
      result.current.stopRecording();
    });

    expect(result.current.isRecording).toBe(false);
  });

  it("startRecording で MediaRecorder が生成される", async () => {
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));

    await act(async () => {
      await result.current.startRecording();
    });

    expect(MockMediaRecorder.instances).toHaveLength(1);
  });

  it("stopRecording しても録音前は何もしない", () => {
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));

    expect(() => {
      act(() => { result.current.stopRecording(); });
    }).not.toThrow();
  });
});

describe("useVoiceRecording — 音声データ送信", () => {
  beforeEach(() => setupMocks());
  afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

  it("stopRecording 後に voice イベントが送信される", async () => {
    const sendJson = vi.fn();
    const { result } = renderHook(() => useVoiceRecording(sendJson));

    await act(async () => { await result.current.startRecording(); });
    await act(async () => {
      result.current.stopRecording();
      // onstop の非同期チェーン (blob.arrayBuffer → btoa → sendJson) が完了するまで待機
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(sendJson).toHaveBeenCalledOnce();
    const call = sendJson.mock.calls[0][0] as { type: string; data: string };
    expect(call.type).toBe("voice");
    expect(typeof call.data).toBe("string");
    expect(call.data.length).toBeGreaterThan(0);
  });

  it("送信データが Base64 文字列である", async () => {
    const sendJson = vi.fn();
    const { result } = renderHook(() => useVoiceRecording(sendJson));

    await act(async () => { await result.current.startRecording(); });
    await act(async () => {
      result.current.stopRecording();
      await new Promise((r) => setTimeout(r, 100));
    });

    if (sendJson.mock.calls.length > 0) {
      const { data } = sendJson.mock.calls[0][0] as { data: string };
      expect(() => atob(data)).not.toThrow();
    }
  });

  it("録音停止後にトラックが解放される", async () => {
    mockTrackStop.mockClear();
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));

    await act(async () => { await result.current.startRecording(); });
    await act(async () => {
      result.current.stopRecording();
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(mockTrackStop).toHaveBeenCalled();
  });
});

describe("useVoiceRecording — マイク拒否", () => {
  afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

  it("マイク拒否時に micAllowed が false になる", async () => {
    setupMocks(false);
    const { result } = renderHook(() => useVoiceRecording(vi.fn()));

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.micAllowed).toBe(false);
  });

  it("マイク拒否時は sendJson が呼ばれない", async () => {
    setupMocks(false);
    const sendJson = vi.fn();
    const { result } = renderHook(() => useVoiceRecording(sendJson));

    await act(async () => { await result.current.startRecording(); });
    await flushAsync();

    expect(sendJson).not.toHaveBeenCalled();
  });
});
