# 評価方法ドキュメント

**Version:** 1.0  
**更新日:** 2026-04-17

---

## 1. 研究目的と仮説

### 1.1 研究目的

マルチモーダル入力（表情・音声・テキスト行動）の統合が、自己申告スコアとの相関において単一モダリティより優れるかを検証する。

### 1.2 主な仮説

| 仮説 | 内容 |
|---|---|
| H1 | 単一モダリティよりマルチモーダル統合の方が自己申告スコアとの相関が高い |
| H2 | 重み付け比率の変更により推定精度が変化する |
| H3 | 状態適応型の対話戦略は固定質問より深い情報を引き出す |

---

## 2. セッションログの構造

各セッション終了時に `data/sessions/{session_id}_{timestamp}.json` として保存されます。

```json
{
  "session_id": "abc123",
  "subject_id": "S001",
  "consent_version": "v1.0",
  "weight_mode": "fixed",
  "weights_used": { "face": 0.35, "voice": 0.45, "text": 0.20 },
  "self_report": {
    "pre_session": 0.6,
    "post_session": 0.7
  },
  "turns": [
    {
      "turn": 1,
      "question": "最近、特に気になっていることはありますか？",
      "answer": "少し疲れています",
      "mental_state": "B",
      "mental_score": 0.65,
      "score_breakdown": {
        "score": 0.65,
        "contributions": { "face": 0.23, "voice": 0.29, "text": 0.13 },
        "weights": { "face": 0.35, "voice": 0.45, "text": 0.20 }
      },
      "metrics": { "face": {...}, "voice": {...}, "text": {...} }
    }
  ]
}
```

---

## 3. 評価指標

### 3.1 推定精度

| 指標 | 計算方法 | 目的 |
|---|---|---|
| Pearson 相関係数 (r) | `corr(mental_score, self_report.post_session)` | 推定スコアと主観的状態の線形相関 |
| Spearman 順位相関 (ρ) | 順位ベースの相関 | 外れ値への耐性を持つ相関 |
| MAE | `mean(|mental_score - self_report.post_session|)` | スコアの平均絶対誤差 |
| RMSE | `sqrt(mean((mental_score - self_report.post_session)^2))` | 大きな誤差を重視した誤差 |

### 3.2 状態分類精度

自己申告スコアをしきい値で状態ラベルに変換し、モデル出力と比較します。

**しきい値変換 (自己申告 → 状態ラベル):**

| 自己申告スコア範囲 | 対応状態 |
|---|---|
| ≥ 0.75 | A |
| ≥ 0.50 | B |
| ≥ 0.25 | C |
| < 0.25 | D-1 または D-2 |

| 指標 | 計算方法 |
|---|---|
| 正解率 (Accuracy) | 正解数 / 全件数 |
| 重み付き F1 スコア | `sklearn.metrics.f1_score(weighted)` |
| 混同行列 | 状態ごとの予測分布を可視化 |

### 3.3 重みモード比較 (H2 検証)

同一被験者データに対して `fixed` / `dynamic` の2条件で `mental_score` を再計算し、相関係数を比較します。

---

## 4. 分析手順

### 4.1 必要なツール

```
Python 3.11+
pandas, numpy, scipy, scikit-learn, matplotlib, seaborn
Jupyter Notebook (notebooks/ ディレクトリ)
```

### 4.2 データ収集

1. `docker compose up` でシステムを起動
2. 各被験者のセッションを実施 (推奨: 1セッション = 5〜10ターン)
3. セッション終了後に `data/sessions/` 配下に JSON が自動保存される
4. 複数セッションを収集後、分析を実施

### 4.3 分析スクリプト例

```python
import json
import glob
import pandas as pd
from scipy import stats

# セッションログを読み込む
records = []
for path in glob.glob("data/sessions/*.json"):
    with open(path) as f:
        data = json.load(f)
    records.append({
        "session_id":    data["session_id"],
        "subject_id":    data["subject_id"],
        "weight_mode":   data["weight_mode"],
        "pre_report":    data["self_report"].get("pre_session"),
        "post_report":   data["self_report"].get("post_session"),
        "final_score":   data["turns"][-1]["mental_score"] if data["turns"] else None,
        "final_state":   data["turns"][-1]["mental_state"] if data["turns"] else None,
        "n_turns":       len(data["turns"]),
    })

df = pd.DataFrame(records).dropna(subset=["post_report", "final_score"])

# H1: マルチモーダル統合 vs 自己申告の相関
r, p = stats.pearsonr(df["final_score"], df["post_report"])
print(f"Pearson r={r:.3f}, p={p:.4f}")

# モダリティ別寄与度の取得
contrib_records = []
for path in glob.glob("data/sessions/*.json"):
    with open(path) as f:
        data = json.load(f)
    for turn in data["turns"]:
        bd = turn.get("score_breakdown", {})
        contrib = bd.get("contributions", {})
        contrib_records.append({
            "session_id":  data["session_id"],
            "turn":        turn["turn"],
            "face_contrib": contrib.get("face"),
            "voice_contrib": contrib.get("voice"),
            "text_contrib":  contrib.get("text"),
            "mental_score":  turn["mental_score"],
        })

contrib_df = pd.DataFrame(contrib_records).dropna()
```

### 4.4 可視化例

```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 推定スコア vs 自己申告スコア
axes[0].scatter(df["final_score"], df["post_report"], alpha=0.7)
axes[0].plot([0, 1], [0, 1], "r--", label="y=x")
axes[0].set_xlabel("Estimated Mental Score")
axes[0].set_ylabel("Self-Report Score (post)")
axes[0].set_title(f"Score Correlation (r={r:.3f})")

# モダリティ別平均寄与度
mean_contrib = contrib_df[["face_contrib", "voice_contrib", "text_contrib"]].mean()
axes[1].bar(["Face", "Voice", "Text"], mean_contrib.values, color=["#4e9e8f", "#2a7c6f", "#c49a2a"])
axes[1].set_ylabel("Mean Contribution")
axes[1].set_title("Average Modality Contribution")

plt.tight_layout()
plt.savefig("docs/figures/evaluation_results.png", dpi=150)
plt.show()
```

---

## 5. 実験プロトコル

### 5.1 セッション設計

| 項目 | 内容 |
|---|---|
| セッション時間 | 5〜10 分 |
| 最大ターン数 | 10 (環境変数 `MAX_TURNS` で変更可) |
| 自己申告タイミング | セッション開始直前 / 終了直後 |
| 推奨被験者数 | 統計的有意性のため 20 名以上 |

### 5.2 実施手順

1. 被験者に研究目的・非医療的用途を説明
2. `subject_id` を割り当てて WebSocket URL に付与
   (`ws://localhost:8000/ws/{uuid}?subject_id=S001`)
3. セッション開始前に自己申告スコアを入力させる (pre_session)
4. 通常の会話を 5〜10 ターン実施
5. セッション終了後に自己申告スコアを入力させる (post_session)
6. `data/sessions/` からログを回収

### 5.3 重みモード比較実験 (H2)

同一被験者に対して `WEIGHT_MODE=fixed` と `WEIGHT_MODE=dynamic` の2条件でセッションを実施し、
各条件での相関係数を比較します。

```bash
# fixed モード
WEIGHT_MODE=fixed docker compose up

# dynamic モード
WEIGHT_MODE=dynamic docker compose up
```

---

## 6. 倫理上の注意事項

- 本システムは**研究用プロトタイプ**であり、医療診断を目的としない
- 収集データは研究目的のみに使用する
- 被験者の同意を得たうえで実施する
- `data/sessions/` ディレクトリは `.gitignore` に追加し、外部公開しない
- 顔画像・音声波形は保存せず、特徴量のみを記録する
