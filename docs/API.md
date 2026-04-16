# API 仕様書

**Version:** 1.0  
**更新日:** 2026-04-17

---

## WebSocket API

### エンドポイント

```
ws://localhost:8000/ws/{session_id}
```

#### パスパラメータ

| 名前 | 型 | 必須 | 説明 |
|---|---|---|---|
| `session_id` | string | ✅ | セッションを一意に識別する ID (例: `uuid-v4`) |

#### クエリパラメータ

| 名前 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `subject_id` | string | `"unknown"` | 研究用被験者 ID |
| `consent_version` | string | `"v1.0"` | 同意書バージョン |

---

### クライアント → サーバー イベント

#### `face` — 表情データ送信

```json
{
  "type": "face",
  "data": {
    "happy":    0.6,
    "angry":    0.05,
    "sad":      0.05,
    "neutral":  0.30,
    "stability": 0.9
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `happy` / `angry` / `sad` / `neutral` | float (0–1) | 各感情の確率 (face-api.js 出力) |
| `stability` | float (0–1) | 直近フレームの支配表情の安定度 |

**レスポンス:** なし

---

#### `voice` — 音声データ送信

```json
{
  "type": "voice",
  "data": "<Base64 エンコードされた WAV バイナリ>"
}
```

サーバー側で librosa を使って特徴量を抽出します。

**レスポンス:** なし

---

#### `text` — テキスト行動メトリクス送信

```json
{
  "type": "text",
  "data": {
    "interval_ms":     120.5,
    "backspace_count": 3,
    "total_keys":      45,
    "idle_ms":         800.0,
    "total_time_ms":   8500.0
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `interval_ms` | float | キー間の平均インターバル (ms) |
| `backspace_count` | int | バックスペース入力回数 |
| `total_keys` | int | 総キー入力数 |
| `idle_ms` | float | 無入力の合計時間 (閾値 2000ms) |
| `total_time_ms` | float | 最初のキー入力からの経過時間 |

**レスポンス:** なし

---

#### `self_report` — 自己申告スコア送信

```json
{
  "type": "self_report",
  "timing": "pre_session",
  "score": 0.65
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `timing` | `"pre_session"` \| `"post_session"` | セッション開始前 / 終了後 |
| `score` | float (0–1) | 自己申告の主観的幸福感スコア |

**レスポンス:** [`ack`](#ack--確認応答)

---

#### `message` — ユーザーメッセージ送信 (グラフ実行)

```json
{
  "type": "message",
  "data": {
    "text": "今日は少し疲れています",
    "input_mode": "text"
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `text` | string | ユーザーの発言テキスト |
| `input_mode` | `"text"` \| `"voice"` | 入力方法 |

**レスポンス:** [`state`](#state--メンタル状態更新) → [`question`](#question--ai-質問) または [`close`](#close--セッション終了)

---

### サーバー → クライアント イベント

#### `ack` — 確認応答

```json
{
  "type": "ack",
  "timing": "pre_session"
}
```

`self_report` イベント受信時に返します。

---

#### `state` — メンタル状態更新

```json
{
  "type": "state",
  "mental_state": "B",
  "score": 0.65,
  "reasoning": "音声から落ち着いた様子が見られます。",
  "score_breakdown": {
    "score": 0.65,
    "contributions": { "face": 0.23, "voice": 0.29, "text": 0.13 },
    "weights":        { "face": 0.35, "voice": 0.45, "text": 0.20 }
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `mental_state` | `"A"` \| `"B"` \| `"C"` \| `"D-1"` \| `"D-2"` | 判定されたメンタル状態 |
| `score` | float (0–1) | 統合スコア |
| `reasoning` | string | LLM が生成した自然言語の判定理由 |
| `score_breakdown.contributions` | object | 各モダリティの加重後スコア |
| `score_breakdown.weights` | object | 使用された重み |

**メンタル状態の定義:**

| 値 | 意味 | スコア範囲 |
|---|---|---|
| `A` | とても良い状態 | ≥ 0.75 |
| `B` | 良い状態 | ≥ 0.50 |
| `C` | 少し気になる | ≥ 0.25 |
| `D-1` | 興奮・怒りが見られる | < 0.25 かつ怒り優位 |
| `D-2` | 落ち込みが見られる | < 0.25 かつ悲しみ優位 |

---

#### `question` — AI 質問

```json
{
  "type": "question",
  "text": "最近、特に気になっていることはありますか？"
}
```

セッションが継続中（ターン数が上限未満）の場合に返します。

---

#### `close` — セッション終了

```json
{
  "type": "close"
}
```

`max_turns` に達した場合、または D-1/D-2 状態と判定された場合に返します。受信後は再送信不可。

---

#### `error` — エラー通知

```json
{
  "type": "error",
  "message": "エラーの詳細メッセージ"
}
```

グラフ実行中に例外が発生した場合に返します。セッションは継続します。

---

### 通信フローの例

```
Client                          Server
  |                               |
  |-- face {happy:0.6, ...} ----> |
  |-- text {interval_ms:120} ---> |
  |-- self_report pre 0.6 ------> |
  |<-- ack {timing:pre_session} --|
  |                               |
  |-- message {text:"こんにちは"} -> | (LangGraph 実行)
  |<-- state {B, 0.65, ...} ------|
  |<-- question {text:"..."} -----|
  |                               |
  |-- message {text:"少し疲れ"} --> | (LangGraph 実行, done=True)
  |<-- state {C, 0.40, ...} ------|
  |<-- close {} -----------------|
  |                               |
  X (切断) → セッションログ保存
```

---

## REST API

### `GET /health`

サービスの死活確認。

**レスポンス:**

```json
{ "status": "ok" }
```

---

### `GET /`

バックエンド起動確認。

**レスポンス:**

```json
{ "message": "Multimodal Mental Agent backend is running." }
```

---

### `GET /docs`

Swagger UI (FastAPI 自動生成)。開発時のみ使用。

---

## 環境変数

| 変数名 | デフォルト | 説明 |
|---|---|---|
| `GEMINI_API_KEY` | — (必須) | Gemini API キー |
| `AIVIS_URL` | `http://host.docker.internal:10101` | AivisSpeech エンドポイント |
| `AIVIS_SPEAKER_ID` | `1` | AivisSpeech 話者 ID |
| `MAX_TURNS` | `10` | セッションの最大ターン数 |
| `DEBUG_MODE` | `false` | デバッグログ出力の有効化 |
| `WEIGHT_MODE` | `fixed` | 重みモード (`fixed` \| `dynamic`) |
