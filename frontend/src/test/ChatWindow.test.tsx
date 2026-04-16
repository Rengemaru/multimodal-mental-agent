import { render, screen, rerender } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ChatWindow, { Message } from "../components/ChatWindow";

// ── モック ────────────────────────────────────────────────────────────────────

const mockSpeak = vi.fn();
const mockCancel = vi.fn();

class MockSpeechSynthesisUtterance {
  text: string;
  lang = "";
  constructor(text: string) {
    this.text = text;
  }
}

beforeEach(() => {
  vi.stubGlobal("speechSynthesis", { speak: mockSpeak, cancel: mockCancel });
  vi.stubGlobal("SpeechSynthesisUtterance", MockSpeechSynthesisUtterance);
  // jsdom は scrollIntoView を実装していないためモックする
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

// ── 表示 ──────────────────────────────────────────────────────────────────────

describe("ChatWindow — 表示", () => {
  it("メッセージなしでレンダリングできる", () => {
    render(<ChatWindow messages={[]} />);
  });

  it("ユーザーメッセージのテキストが表示される", () => {
    const msgs: Message[] = [{ role: "user", text: "こんにちは" }];
    render(<ChatWindow messages={msgs} />);
    expect(screen.getByText("こんにちは")).toBeInTheDocument();
  });

  it("AI メッセージのテキストが表示される", () => {
    const msgs: Message[] = [{ role: "ai", text: "最近どうですか？" }];
    render(<ChatWindow messages={msgs} />);
    expect(screen.getByText("最近どうですか？")).toBeInTheDocument();
  });

  it("ユーザーと AI のメッセージを data-role 属性で区別する", () => {
    const msgs: Message[] = [
      { role: "user", text: "user msg" },
      { role: "ai", text: "ai msg" },
    ];
    render(<ChatWindow messages={msgs} />);
    const userEl = screen.getByText("user msg").closest("[data-role]");
    const aiEl = screen.getByText("ai msg").closest("[data-role]");
    expect(userEl?.getAttribute("data-role")).toBe("user");
    expect(aiEl?.getAttribute("data-role")).toBe("ai");
  });

  it("複数メッセージをすべて表示する", () => {
    const msgs: Message[] = [
      { role: "user", text: "msg1" },
      { role: "ai", text: "msg2" },
      { role: "user", text: "msg3" },
    ];
    render(<ChatWindow messages={msgs} />);
    expect(screen.getByText("msg1")).toBeInTheDocument();
    expect(screen.getByText("msg2")).toBeInTheDocument();
    expect(screen.getByText("msg3")).toBeInTheDocument();
  });
});

// ── TTS ───────────────────────────────────────────────────────────────────────

describe("ChatWindow — TTS", () => {
  it("AI メッセージ追加時に speak が呼ばれる", () => {
    const msgs: Message[] = [{ role: "ai", text: "最近どうですか？" }];
    render(<ChatWindow messages={msgs} />);
    expect(mockSpeak).toHaveBeenCalledOnce();
  });

  it("speak 前に cancel が呼ばれる", () => {
    const msgs: Message[] = [{ role: "ai", text: "どうぞ" }];
    render(<ChatWindow messages={msgs} />);
    expect(mockCancel).toHaveBeenCalled();
  });

  it("ユーザーメッセージでは speak が呼ばれない", () => {
    const msgs: Message[] = [{ role: "user", text: "こんにちは" }];
    render(<ChatWindow messages={msgs} />);
    expect(mockSpeak).not.toHaveBeenCalled();
  });

  it("最後の AI メッセージのテキストが発話される", () => {
    const msgs: Message[] = [
      { role: "ai", text: "最初の質問" },
      { role: "user", text: "回答" },
      { role: "ai", text: "次の質問" },
    ];
    render(<ChatWindow messages={msgs} />);
    const utterance = mockSpeak.mock.calls[0][0] as MockSpeechSynthesisUtterance;
    expect(utterance.text).toBe("次の質問");
  });

  it("messages が更新されたとき新しい AI メッセージを読み上げる", () => {
    const { rerender } = render(<ChatWindow messages={[]} />);
    expect(mockSpeak).not.toHaveBeenCalled();

    rerender(
      <ChatWindow messages={[{ role: "ai", text: "新しい質問" }]} />
    );
    expect(mockSpeak).toHaveBeenCalledOnce();
  });
});
