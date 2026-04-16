# multimodal-mental-agent

マルチモーダル入力（表情・音声・テキスト行動）からリアルタイムでメンタル状態を推定し、対話を通じてユーザーの状態を分析する研究用プロトタイプです。

> **注意:** 本システムは医療診断を目的としません。対話支援・状態把握のための研究用プロトタイプです。

---

## セットアップ → 起動 → 使い方

### 1. 前提条件

- Docker Desktop (Windows) がインストール済み
- AivisSpeech がホスト側で起動済み (ポート 10101)
- Gemini API キーを取得済み

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して GEMINI_API_KEY を設定する
```

`.env` の内容:

```bash
GEMINI_API_KEY=your_api_key_here
AIVIS_URL=http://host.docker.internal:10101
AIVIS_SPEAKER_ID=1
MAX_TURNS=10
DEBUG_MODE=false
WEIGHT_MODE=fixed   # fixed | dynamic
```

### 3. face-api.js モデルのダウンロード

```bash
# frontend/public/models/ に以下のファイルを配置する
# https://github.com/justadudewhohacks/face-api.js/tree/master/weights から取得
#
# 必要なファイル:
#   tiny_face_detector_model-weights_manifest.json
#   tiny_face_detector_model-shard1
#   face_expression_model-weights_manifest.json
#   face_expression_model-shard1
```

### 4. 起動

```bash
docker compose up --build
```

| サービス | URL |
|---|---|
| フロントエンド | http://localhost:3000 |
| バックエンド API | http://localhost:8000/docs |

### 5. 使い方

1. http://localhost:3000 をブラウザで開く
2. カメラ・マイクの使用許可を許可する
3. セッション開始前に自己申告スコア (0.0〜1.0) を入力して送信
4. AI の質問に答えながら会話を進める
5. セッション終了後に再度自己申告スコアを入力
6. セッションログが `data/sessions/` に自動保存される

**デバッグモード:** URL に `?debug=true` を付けるとスコア内訳・寄与度・重み・判定理由が表示されます。

---

## アーキテクチャ

```
Browser
  ├── face-api.js     ── 1秒ごとに表情スコアを WebSocket 送信
  ├── MediaRecorder   ── 発話後に音声 (Base64 WAV) を送信
  └── useTextBehavior ── キーストロークメトリクスを送信

WebSocket /ws/{session_id}
  └── FastAPI
        └── LangGraph StateGraph
              ├── analysis_node  ── スコア計算 (face/voice/text 統合)
              ├── reasoning_node ── Gemini で判定理由を生成
              ├── question_node  ── Gemini で次の質問を生成
              ├── routing_node   ── 継続 / 終了の分岐
              └── close_node     ── セッション終了処理
```

---

## ディレクトリ構成

```
.
├── docker-compose.yml
├── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     # ChatWindow, StateExplanation, DebugPanel, ...
│   │   ├── hooks/          # useWebSocket, useFaceAnalysis, useVoiceRecording, useTextBehavior
│   │   └── types/          # WebSocket イベント型定義
│   └── public/models/      # face-api.js モデルファイル (手動配置)
├── backend/
│   ├── app/
│   │   ├── agents/         # LangGraph StateGraph + ノード
│   │   ├── models/         # Pydantic モデル
│   │   ├── routers/        # WebSocket エンドポイント
│   │   └── services/       # Gemini, AivisSpeech, librosa, scoring
│   └── tests/              # pytest (カバレッジ 100%)
├── data/sessions/          # セッションログ保存先 (.gitignore 対象)
└── docs/
    ├── API.md              # WebSocket / REST API 仕様
    ├── EVALUATION.md       # 評価方法・分析手順
    └── E2E_CHECKLIST.md    # E2E 手動確認チェックリスト
```

---

## テスト

```bash
# バックエンド (カバレッジ 100%)
docker compose run --rm backend pytest --cov=app

# フロントエンド (82 テスト)
cd frontend && npm test
```

---

## ドキュメント

| ファイル | 内容 |
|---|---|
| [docs/API.md](docs/API.md) | WebSocket / REST API の全イベント仕様 |
| [docs/EVALUATION.md](docs/EVALUATION.md) | 評価指標・分析手順・実験プロトコル |
| [docs/E2E_CHECKLIST.md](docs/E2E_CHECKLIST.md) | 全フロー手動確認チェックリスト |
