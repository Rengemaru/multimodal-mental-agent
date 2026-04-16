// Task 7.3: デバッグパネルコンポーネント
// ?debug=true で表示。スコア内訳・寄与度・重み・判定理由を全表示する。

interface ScoreBreakdown {
  contributions: { face: number; voice: number; text: number };
  weights: { face: number; voice: number; text: number };
}

interface Props {
  mentalState: string;
  score: number;
  reasoning: string;
  scoreBreakdown: ScoreBreakdown;
  visible?: boolean;
}

const MODALITIES = ["face", "voice", "text"] as const;

export default function DebugPanel({
  mentalState,
  score,
  reasoning,
  scoreBreakdown,
  visible = true,
}: Props) {
  if (!visible) return null;

  return (
    <div
      style={{
        padding: "12px 16px",
        borderRadius: 8,
        background: "#1e1e1e",
        color: "#d4d4d4",
        fontFamily: "monospace",
        fontSize: "0.8rem",
        lineHeight: 1.6,
        border: "1px solid #444",
      }}
    >
      {/* タイトル */}
      <p style={{ margin: "0 0 8px", fontWeight: "bold", color: "#9cdcfe" }}>
        🛠 Debug Panel
      </p>

      {/* 判定状態 & スコア */}
      <div style={{ marginBottom: 8 }}>
        <span style={{ color: "#ce9178" }}>mentalState: </span>
        <span style={{ color: "#4ec9b0" }}>{mentalState}</span>
        {"  "}
        <span style={{ color: "#ce9178" }}>score: </span>
        <span style={{ color: "#b5cea8" }}>{score.toFixed(2)}</span>
      </div>

      {/* 内訳テーブル */}
      <table style={{ borderCollapse: "collapse", width: "100%", marginBottom: 8 }}>
        <thead>
          <tr>
            <th style={thStyle}>modality</th>
            <th style={thStyle}>weight</th>
            <th style={thStyle}>contribution</th>
          </tr>
        </thead>
        <tbody>
          {MODALITIES.map((key) => (
            <tr key={key}>
              <td style={tdStyle}>{key}</td>
              <td style={tdStyle}>{scoreBreakdown.weights[key].toFixed(2)}</td>
              <td style={tdStyle}>{scoreBreakdown.contributions[key].toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 判定理由 */}
      <div>
        <span style={{ color: "#ce9178" }}>reasoning: </span>
        <span>{reasoning}</span>
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "2px 8px 2px 0",
  color: "#9cdcfe",
  borderBottom: "1px solid #444",
};

const tdStyle: React.CSSProperties = {
  padding: "2px 8px 2px 0",
  color: "#d4d4d4",
};
