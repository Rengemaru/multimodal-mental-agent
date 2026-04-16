import { useEffect, useRef } from "react";

export interface Message {
  role: "user" | "ai";
  text: string;
}

interface Props {
  messages: Message[];
}

export default function ChatWindow({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // 新しい AI メッセージを TTS で読み上げる
  useEffect(() => {
    const last = messages[messages.length - 1];
    if (last?.role === "ai" && typeof window.speechSynthesis !== "undefined") {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(last.text);
      utterance.lang = "ja-JP";
      window.speechSynthesis.speak(utterance);
    }
  }, [messages]);

  // 末尾へ自動スクロール
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: "16px 0",
        overflowY: "auto",
        maxHeight: "60vh",
      }}
    >
      {messages.map((msg, i) => (
        <div
          key={i}
          data-role={msg.role}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: msg.role === "user" ? "flex-end" : "flex-start",
            gap: 4,
          }}
        >
          <span
            style={{
              fontSize: "0.75rem",
              color: "#888",
              paddingInline: 4,
            }}
          >
            {msg.role === "ai" ? "AI" : "あなた"}
          </span>
          <p
            style={{
              margin: 0,
              padding: "10px 14px",
              borderRadius: 16,
              maxWidth: "75%",
              lineHeight: 1.6,
              background: msg.role === "ai" ? "#ecf6f5" : "#2a7c6f",
              color: msg.role === "ai" ? "#16302b" : "#fff",
            }}
          >
            {msg.text}
          </p>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
