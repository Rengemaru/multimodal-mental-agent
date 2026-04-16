import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import SelfReportSlider from "../components/SelfReportSlider";

const SUBMIT_BTN = /送信/;

describe("SelfReportSlider — 表示", () => {
  it("スライダーが表示される", () => {
    render(<SelfReportSlider timing="pre_session" onSubmit={vi.fn()} />);
    expect(screen.getByRole("slider")).toBeInTheDocument();
  });

  it("pre_session のラベルが表示される", () => {
    render(<SelfReportSlider timing="pre_session" onSubmit={vi.fn()} />);
    expect(screen.getByText(/セッション開始前/)).toBeInTheDocument();
  });

  it("post_session のラベルが表示される", () => {
    render(<SelfReportSlider timing="post_session" onSubmit={vi.fn()} />);
    expect(screen.getByText(/セッション終了後/)).toBeInTheDocument();
  });

  it("初期値が 0.5 である", () => {
    render(<SelfReportSlider timing="pre_session" onSubmit={vi.fn()} />);
    expect(screen.getByRole("slider")).toHaveValue("0.5");
  });

  it("送信ボタンが表示される", () => {
    render(<SelfReportSlider timing="pre_session" onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: SUBMIT_BTN })).toBeInTheDocument();
  });
});

describe("SelfReportSlider — 操作", () => {
  it("スライダーの値を変更できる", () => {
    render(<SelfReportSlider timing="pre_session" onSubmit={vi.fn()} />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "0.8" } });
    expect(slider).toHaveValue("0.8");
  });

  it("値を変更すると表示が更新される", () => {
    render(<SelfReportSlider timing="pre_session" onSubmit={vi.fn()} />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "0.7" } });
    expect(screen.getByText(/0\.7/)).toBeInTheDocument();
  });

  it("送信ボタンで onSubmit が現在の値(数値)で呼ばれる", () => {
    const onSubmit = vi.fn();
    render(<SelfReportSlider timing="pre_session" onSubmit={onSubmit} />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "0.8" } });
    fireEvent.click(screen.getByRole("button", { name: SUBMIT_BTN }));
    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit).toHaveBeenCalledWith(0.8);
  });

  it("デフォルト値 0.5 のまま送信できる", () => {
    const onSubmit = vi.fn();
    render(<SelfReportSlider timing="post_session" onSubmit={onSubmit} />);
    fireEvent.click(screen.getByRole("button", { name: SUBMIT_BTN }));
    expect(onSubmit).toHaveBeenCalledWith(0.5);
  });

  it("0.0 〜 1.0 の範囲の値を送信できる", () => {
    const onSubmit = vi.fn();
    render(<SelfReportSlider timing="pre_session" onSubmit={onSubmit} />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "0.0" } });
    fireEvent.click(screen.getByRole("button", { name: SUBMIT_BTN }));
    expect(onSubmit).toHaveBeenCalledWith(0.0);
  });
});
