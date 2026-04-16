import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useWebSocket } from "../hooks/useWebSocket";

// ── MockWebSocket ─────────────────────────────────────────────────────────────

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  static instances: MockWebSocket[] = [];

  url: string;
  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close"));
  }

  // テストヘルパー
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event("open"));
  }

  simulateMessage(data: object) {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }));
  }

  simulateError() {
    this.onerror?.(new Event("error"));
  }
}

// ── セットアップ ───────────────────────────────────────────────────────────────

const TEST_URL = "ws://localhost:8000/ws/test-session";

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

// ── 接続 ──────────────────────────────────────────────────────────────────────

describe("useWebSocket — 接続", () => {
  it("マウント時に WebSocket 接続を開始する", () => {
    renderHook(() => useWebSocket(TEST_URL));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toBe(TEST_URL);
  });

  it("接続確立前は isConnected が false", () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    expect(result.current.isConnected).toBe(false);
  });

  it("接続確立後に isConnected が true になる", async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });

    expect(result.current.isConnected).toBe(true);
  });

  it("切断後に isConnected が false になる", async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });
    expect(result.current.isConnected).toBe(true);

    await act(async () => {
      MockWebSocket.instances[0].close();
    });

    expect(result.current.isConnected).toBe(false);
  });

  it("アンマウント時に WebSocket を閉じる", async () => {
    const { unmount } = renderHook(() => useWebSocket(TEST_URL));
    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });

    unmount();

    expect(MockWebSocket.instances[0].readyState).toBe(MockWebSocket.CLOSED);
  });
});

// ── 送受信 ────────────────────────────────────────────────────────────────────

describe("useWebSocket — 送受信", () => {
  it("sendJson が接続中に JSON を送信する", async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      result.current.sendJson({ type: "message", data: { text: "こんにちは" } });
    });

    expect(MockWebSocket.instances[0].sentMessages).toHaveLength(1);
    expect(JSON.parse(MockWebSocket.instances[0].sentMessages[0])).toEqual({
      type: "message",
      data: { text: "こんにちは" },
    });
  });

  it("sendJson が未接続時に何もしない", () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    act(() => {
      result.current.sendJson({ type: "test" });
    });

    expect(MockWebSocket.instances[0].sentMessages).toHaveLength(0);
  });

  it("サーバーからのメッセージを lastMessage に格納する", async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
      MockWebSocket.instances[0].simulateMessage({ type: "state", mental_state: "B" });
    });

    expect(result.current.lastMessage).toEqual({ type: "state", mental_state: "B" });
  });

  it("不正な JSON を受け取っても lastMessage が変わらない", async () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));

    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await act(async () => {
      MockWebSocket.instances[0].onmessage?.(
        new MessageEvent("message", { data: "not-json" })
      );
    });

    expect(result.current.lastMessage).toBeNull();
  });
});

// ── 自動再接続 ────────────────────────────────────────────────────────────────

describe("useWebSocket — 自動再接続", () => {
  it("切断後に自動再接続を試みる", async () => {
    vi.useFakeTimers();

    renderHook(() => useWebSocket(TEST_URL));
    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });

    await act(async () => {
      MockWebSocket.instances[0].close();
    });
    expect(MockWebSocket.instances).toHaveLength(1);

    await act(async () => {
      vi.advanceTimersByTime(3100);
    });

    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it("アンマウント後は再接続しない", async () => {
    vi.useFakeTimers();

    const { unmount } = renderHook(() => useWebSocket(TEST_URL));
    await act(async () => {
      MockWebSocket.instances[0].simulateOpen();
    });

    unmount();

    await act(async () => {
      vi.advanceTimersByTime(3100);
    });

    // アンマウント後なので新しいインスタンスは作られない
    expect(MockWebSocket.instances).toHaveLength(1);
  });
});
