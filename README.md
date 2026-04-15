# multimodal-mental-agent

マルチモーダル入力を使ってメンタル状況を把握し、対話的に質問・説明を行う研究向けプロトタイプです。

## 概要

- フロントエンド: React + Vite + TypeScript
- バックエンド: FastAPI + LangGraph
- 通信: WebSocket
- マルチモーダル入力: 表情、音声、テキスト、自己申告スコア
- 実行環境: Docker Compose

## 予定ディレクトリ構成

```text
.
|-- backend/
|   |-- app/
|   |   |-- agents/
|   |   |-- models/
|   |   |-- routers/
|   |   `-- services/
|   `-- tests/
|-- data/
|   `-- sessions/
|-- docs/
`-- frontend/
    |-- public/
    |   `-- models/
    `-- src/
        |-- components/
        |-- hooks/
        |-- styles/
        `-- types/
```

## セットアップ予定

1. `.env.example` を元に `.env` を作成します。
2. Docker / Docker Compose が使えることを確認します。
3. 今後 `docker compose up --build` で全サービスを起動できる構成にします。

現時点では `Task 0.1` として、初期構成と設定ファイルの土台までを用意しています。
