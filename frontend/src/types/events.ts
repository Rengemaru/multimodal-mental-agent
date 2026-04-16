// WebSocket イベント型定義
// バックエンドの app/routers/websocket.py のプロトコルに対応

// ── クライアント → サーバー ───────────────────────────────────────────────────

export interface FaceEvent {
  type: "face";
  data: {
    happy: number;
    angry: number;
    sad: number;
    neutral: number;
    stability: number;
  };
}

export interface VoiceEvent {
  type: "voice";
  data: string; // Base64 WAV
}

export interface TextEvent {
  type: "text";
  data: {
    interval_ms: number;
    backspace_count: number;
    total_keys: number;
    idle_ms: number;
    total_time_ms: number;
  };
}

export interface SelfReportEvent {
  type: "self_report";
  timing: "pre_session" | "post_session";
  score: number; // 0.0 - 1.0
}

export interface MessageEvent {
  type: "message";
  data: {
    text: string;
    input_mode: "voice" | "text";
  };
}

export type ClientEvent = FaceEvent | VoiceEvent | TextEvent | SelfReportEvent | MessageEvent;

// ── サーバー → クライアント ───────────────────────────────────────────────────

export interface AckEvent {
  type: "ack";
  timing: "pre_session" | "post_session";
}

export interface StateEvent {
  type: "state";
  mental_state: string; // "A" | "B" | "C" | "D-1" | "D-2"
  score: number;
  reasoning: string;
  score_breakdown: Record<string, unknown>;
}

export interface QuestionEvent {
  type: "question";
  text: string;
}

export interface CloseEvent {
  type: "close";
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type ServerEvent = AckEvent | StateEvent | QuestionEvent | CloseEvent | ErrorEvent;
