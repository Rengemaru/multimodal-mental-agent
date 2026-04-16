import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StateExplanation from "../components/StateExplanation";

const BASE_PROPS = {
  mentalState: "B",
  score: 0.65,
  reasoning: "全体的に落ち着いた様子が見られます。",
};

const BREAKDOWN = {
  contributions: { face: 0.23, voice: 0.29, text: 0.13 },
  weights: { face: 0.35, voice: 0.45, text: 0.20 },
};

// ── 表示 ──────────────────────────────────────────────────────────────────────

describe("StateExplanation — 表示", () => {
  it("クラッシュせずにレンダリングできる", () => {
    render(<StateExplanation {...BASE_PROPS} />);
  });

  it("推定理由のテキストが表示される", () => {
    render(<StateExplanation {...BASE_PROPS} />);
    expect(screen.getByText(BASE_PROPS.reasoning)).toBeInTheDocument();
  });

  it("スコアがパーセントで表示される", () => {
    render(<StateExplanation {...BASE_PROPS} score={0.65} />);
    expect(screen.getByText(/65/)).toBeInTheDocument();
  });
});

// ── メンタル状態ラベル ─────────────────────────────────────────────────────────

describe("StateExplanation — 状態ラベル", () => {
  const cases: [string, RegExp][] = [
    ["A",   /とても良い/],
    ["B",   /良い状態/],
    ["C",   /少し気になる/],
    ["D-1", /興奮・怒り/],
    ["D-2", /落ち込み/],
  ];

  cases.forEach(([state, labelPattern]) => {
    it(`mentalState="${state}" に対応する日本語ラベルが表示される`, () => {
      render(<StateExplanation {...BASE_PROPS} mentalState={state} />);
      expect(screen.getByText(labelPattern)).toBeInTheDocument();
    });
  });
});

// ── スコア内訳 ────────────────────────────────────────────────────────────────

describe("StateExplanation — スコア内訳", () => {
  it("scoreBreakdown が渡されると表情・音声・テキストの寄与が表示される", () => {
    render(<StateExplanation {...BASE_PROPS} scoreBreakdown={BREAKDOWN} />);
    expect(screen.getByText(/表情/)).toBeInTheDocument();
    expect(screen.getByText(/音声/)).toBeInTheDocument();
    expect(screen.getByText(/テキスト/)).toBeInTheDocument();
  });

  it("scoreBreakdown が渡されないと内訳が表示されない", () => {
    render(<StateExplanation {...BASE_PROPS} />);
    expect(screen.queryByText(/表情/)).not.toBeInTheDocument();
  });
});
