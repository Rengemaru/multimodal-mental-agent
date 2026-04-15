const cards = [
  "Face analysis hook placeholder",
  "Voice recording pipeline placeholder",
  "Text behavior analysis placeholder",
];

export default function App() {
  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "48px 24px",
        background:
          "linear-gradient(135deg, rgb(247 244 234), rgb(222 237 241) 55%, rgb(253 225 210))",
        color: "#16302b",
        fontFamily: '"Segoe UI", sans-serif',
      }}
    >
      <section
        style={{
          margin: "0 auto",
          maxWidth: 920,
          background: "rgba(255, 255, 255, 0.85)",
          border: "1px solid rgba(22, 48, 43, 0.12)",
          borderRadius: 24,
          padding: 32,
          boxShadow: "0 18px 48px rgba(22, 48, 43, 0.12)",
        }}
      >
        <p style={{ letterSpacing: "0.18em", textTransform: "uppercase", margin: 0 }}>
          Task 0.2 Bootstrap
        </p>
        <h1 style={{ fontSize: "clamp(2.5rem, 5vw, 4.5rem)", marginBottom: 12 }}>
          Multimodal Mental Agent
        </h1>
        <p style={{ fontSize: "1.1rem", lineHeight: 1.7, maxWidth: 700 }}>
          Docker Compose でフロントエンドとバックエンドを同時起動できる最小構成です。
          後続タスクで face-api.js、Gemini、LangGraph の本実装を追加していきます。
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 16,
            marginTop: 32,
          }}
        >
          {cards.map((card) => (
            <article
              key={card}
              style={{
                padding: 20,
                borderRadius: 20,
                background: "rgba(236, 246, 245, 0.9)",
                border: "1px solid rgba(22, 48, 43, 0.12)",
              }}
            >
              <h2 style={{ fontSize: "1rem", margin: 0 }}>{card}</h2>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
