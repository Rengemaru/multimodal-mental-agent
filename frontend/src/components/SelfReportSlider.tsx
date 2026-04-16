import { useState } from "react";

interface Props {
  timing: "pre_session" | "post_session";
  onSubmit: (score: number) => void;
}

const TIMING_LABEL: Record<string, string> = {
  pre_session: "セッション開始前",
  post_session: "セッション終了後",
};

export default function SelfReportSlider({ timing, onSubmit }: Props) {
  const [score, setScore] = useState(0.5);

  return (
    <div style={{ padding: "24px", textAlign: "center" }}>
      <p style={{ marginBottom: 16, fontWeight: "bold" }}>
        {TIMING_LABEL[timing]}の気分を教えてください
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: 12, justifyContent: "center" }}>
        <span>😔</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={score}
          onChange={(e) => setScore(parseFloat(e.target.value))}
          style={{ width: 240 }}
        />
        <span>😊</span>
      </div>

      <p style={{ marginTop: 8, fontSize: "1.2rem" }}>{score.toFixed(2)}</p>

      <button
        onClick={() => onSubmit(score)}
        style={{
          marginTop: 16,
          padding: "8px 32px",
          borderRadius: 8,
          border: "none",
          background: "#2a7c6f",
          color: "#fff",
          cursor: "pointer",
          fontSize: "1rem",
        }}
      >
        送信
      </button>
    </div>
  );
}
