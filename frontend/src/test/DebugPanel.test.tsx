import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import DebugPanel from "../components/DebugPanel";

const BREAKDOWN = {
  contributions: { face: 0.23, voice: 0.29, text: 0.13 },
  weights: { face: 0.35, voice: 0.45, text: 0.20 },
};

const BASE_PROPS = {
  mentalState: "B",
  score: 0.65,
  reasoning: "全体的に落ち着いた様子が見られます。",
  scoreBreakdown: BREAKDOWN,
};

// ── 表示 ──────────────────────────────────────────────────────────────────────

describe("DebugPanel — 表示", () => {
  it("クラッシュせずにレンダリングできる", () => {
    render(<DebugPanel {...BASE_PROPS} />);
  });

  it("デバッグパネルのタイトルが表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    expect(screen.getByText(/Debug/i)).toBeInTheDocument();
  });

  it("判定状態が表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    expect(screen.getByText(/B/)).toBeInTheDocument();
  });

  it("スコアが数値で表示される", () => {
    render(<DebugPanel {...BASE_PROPS} score={0.65} />);
    expect(screen.getByText(/0\.65/)).toBeInTheDocument();
  });

  it("判定理由テキストが表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    expect(screen.getByText(BASE_PROPS.reasoning)).toBeInTheDocument();
  });
});

// ── スコア内訳 ────────────────────────────────────────────────────────────────

describe("DebugPanel — スコア内訳", () => {
  it("各モダリティの寄与度が数値で表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    // contributions: face=0.23, voice=0.29, text=0.13
    expect(screen.getByText(/0\.23/)).toBeInTheDocument();
    expect(screen.getByText(/0\.29/)).toBeInTheDocument();
    expect(screen.getByText(/0\.13/)).toBeInTheDocument();
  });

  it("各モダリティの重みが数値で表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    // weights: face=0.35, voice=0.45, text=0.20
    expect(screen.getByText(/0\.35/)).toBeInTheDocument();
    expect(screen.getByText(/0\.45/)).toBeInTheDocument();
    expect(screen.getByText(/0\.20/)).toBeInTheDocument();
  });

  it("モダリティラベル (face/voice/text) が表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    expect(screen.getByText(/face/i)).toBeInTheDocument();
    expect(screen.getByText(/voice/i)).toBeInTheDocument();
    expect(screen.getByText(/text/i)).toBeInTheDocument();
  });
});

// ── URL パラメータ連携 ─────────────────────────────────────────────────────────

describe("DebugPanel — visible prop", () => {
  it("visible=true のときレンダリングされる", () => {
    render(<DebugPanel {...BASE_PROPS} visible={true} />);
    expect(screen.getByText(/Debug/i)).toBeInTheDocument();
  });

  it("visible=false のとき何も表示されない", () => {
    render(<DebugPanel {...BASE_PROPS} visible={false} />);
    expect(screen.queryByText(/Debug/i)).not.toBeInTheDocument();
  });

  it("visible を省略したときデフォルトで表示される", () => {
    render(<DebugPanel {...BASE_PROPS} />);
    expect(screen.getByText(/Debug/i)).toBeInTheDocument();
  });
});
