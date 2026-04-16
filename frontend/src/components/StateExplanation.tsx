// Task 7.2: メンタル状態の説明コンポーネント
// 数値を使わず言語化された説明でユーザーに状態を伝える

interface ScoreBreakdown {
  contributions: { face: number; voice: number; text: number };
  weights: { face: number; voice: number; text: number };
}

interface Props {
  mentalState: string;
  score: number;
  reasoning: string;
  scoreBreakdown?: ScoreBreakdown;
}

const STATE_LABEL: Record<string, { label: string; color: string }> = {
  A:   { label: "とても良い状態です",       color: "#2a7c6f" },
  B:   { label: "良い状態です",             color: "#4a9e8f" },
  C:   { label: "少し気になる点があります",  color: "#c49a2a" },
  "D-1": { label: "興奮・怒りが見られます", color: "#c45a2a" },
  "D-2": { label: "落ち込みが見られます",   color: "#6a5a9e" },
};

const MODALITY_LABEL: Record<string, string> = {
  face: "表情",
  voice: "音声",
  text: "テキスト",
};

export default function StateExplanation({
  mentalState,
  score,
  reasoning,
  scoreBreakdown,
}: Props) {
  const stateInfo = STATE_LABEL[mentalState] ?? { label: mentalState, color: "#888" };
  const scorePercent = Math.round(score * 100);

  return (
    <div
      style={{
        padding: "16px 20px",
        borderRadius: 16,
        background: "rgba(255,255,255,0.85)",
        border: `2px solid ${stateInfo.color}`,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      {/* 状態ラベル */}
      <p
        style={{
          margin: 0,
          fontWeight: "bold",
          fontSize: "1.1rem",
          color: stateInfo.color,
        }}
      >
        {stateInfo.label}
      </p>

      {/* スコアバー */}
      <div>
        <div
          style={{
            height: 8,
            borderRadius: 4,
            background: "#e0e0e0",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${scorePercent}%`,
              background: stateInfo.color,
              borderRadius: 4,
              transition: "width 0.4s ease",
            }}
          />
        </div>
        <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "#888", textAlign: "right" }}>
          {scorePercent}%
        </p>
      </div>

      {/* 推定理由 */}
      <p style={{ margin: 0, lineHeight: 1.7, color: "#333" }}>{reasoning}</p>

      {/* スコア内訳（オプション） */}
      {scoreBreakdown && (
        <div style={{ borderTop: "1px solid #e0e0e0", paddingTop: 10 }}>
          {(["face", "voice", "text"] as const).map((key) => {
            const contribution = scoreBreakdown.contributions[key];
            const pct = Math.round(contribution * 100);
            return (
              <div
                key={key}
                style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}
              >
                <span style={{ width: 52, fontSize: "0.8rem", color: "#555" }}>
                  {MODALITY_LABEL[key]}
                </span>
                <div
                  style={{
                    flex: 1,
                    height: 6,
                    borderRadius: 3,
                    background: "#e0e0e0",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${Math.min(pct * 2, 100)}%`,
                      background: stateInfo.color,
                      opacity: 0.7,
                    }}
                  />
                </div>
                <span style={{ width: 36, fontSize: "0.8rem", color: "#888", textAlign: "right" }}>
                  {pct}%
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
