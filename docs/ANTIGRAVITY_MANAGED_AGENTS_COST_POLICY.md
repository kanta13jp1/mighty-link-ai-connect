# Antigravity 2.0 Managed Agents 料金・利用条件および監視ポリシー

> [!NOTE]
> 本書は、Google Vertex AI Agent Builder（Gemini Enterprise Agent Platform）における Managed Agents の最新料金体系に基づき、Mighty Skill-Bridge プロジェクトにおける正式採用前のコスト監視体制、Express Mode からの Tier 移行リスク、およびコスト最適化方針を定めたものです。

---

## 1. 公式料金体系（Vertex AI Agent Builder 準拠）

Managed Agents の実行コストは、以下の複数の課金次元（Billing Dimensions）の合算によって pay-as-you-go（従量課金）で計算されます。

### ① Agent Engine Runtime (コンピューティング & メモリ)

エージェントがアクティブに稼働・処理しているランタイム時間（Active vCPU-hour）に対して課金されます。**アイドル状態（待機時）は課金されません**。

- **vCPU 料金**: `$0.0864` / vCPU-hour
- **メモリ料金**: `$0.0090` / GB-hour

### ② Sessions & Memory Bank (セッション追跡 & 長期記憶)

エージェントが会話履歴（Session）を維持したり、長期記憶（Memory Bank）へイベントを格納・検索するたびに課金されます。

- **セッションイベント料金**: `$0.25` / 1,000 events

### ③ Vertex AI Search (グラウンディング & ドキュメント検索)

ドキュメント（経歴書、docs、仕様書）を読み込んで回答を生成（RAG/Grounding）する検索クエリ数に応じて課金されます。

- **Standard Search (標準検索)**: `$1.50` / 1,000 queries
- **Enterprise Search (生成要約付き)**: `$4.00` / 1,000 queries
- **Conversational Queries (会話型RAG)**: `$6.00` / 1,000 requests

### ④ Foundation Model Tokens (Gemini モデル使用料)

エージェントの内部思考やプロンプト処理に使用される Gemini 3.1 Pro などのトークン使用料です（Gemini API 料金に準拠）。

- **Gemini 3.1 Pro (入力)**: `$0.00125` / 1,000 tokens (128k context)
- **Gemini 3.1 Pro (出力)**: `$0.00375` / 1,000 tokens

---

## 2. 利用条件 & 無料枠 (Free Tiers)

正式採用前の検証・PoCフェーズにおけるコストを最小化するため、以下の無料枠と制限を活用します。

- **新規 Google Cloud 無料クレジット**: `$300` (90日間有効)
- **Express Mode (無料お試し)**:
  - 課金登録なしで最大 **10個の Agent Engine** を作成可能。
  - **90日間**の評価利用が可能。
- **Vertex AI Search 無料クエリ枠**: 毎月 **10,000 クエリ** まで無料。

---

## 3. コストシミュレーション & Tier 移行監視

本プロジェクトにおける、エージェント1個あたりの月額コスト想定シナリオです。

### 📊 シミュレーション・シナリオ (月間アクティブ 20時間、10,000セッション、RAG検索 5,000回想定)

| 課金項目 | 単価 | 想定月間使用量 | 想定月額コスト |
|---|---|---|---|
| **vCPU Runtime** | $0.0864 / vCPU-hour | 2 vCPU × 20時間 = 40 vCPU-h | **$3.46** |
| **Memory Runtime** | $0.0090 / GB-hour | 8 GB × 20時間 = 160 GB-h | **$1.44** |
| **Sessions Event** | $0.25 / 1,000 events | 10,000 events | **$2.50** |
| **Vertex AI Search** | $4.00 / 1,000 queries | 5,000 queries | **$20.00** |
| **Gemini 3.1 Pro (RAG)** | Input/Output Token | 入力10M / 出力2M tokens | **$20.00** |
| **合計想定コスト** | - | - | **$47.40** / 月 (約 7,110円) |

### 🚨 監視アラート (Tier Switch) しきい値

Express Mode の終了時、または Enterprise への正式採用に伴う課金開始の際、予期せぬ超過を防ぐための監視ルールを適用します。

1. **日次予算アラート (GCP Billing Alert)**: プロジェクト全体で **1日あたり $5.00**、または**月間 $100.00** に到達した時点で自動メール通知および API 遮断（サーキットブレーカー）。
2. **セクションイベント限界値**: 1つの会話セッション中の履歴記憶イベントが **50件** を超えた場合、自動的に古いコンテキストを要約し、Session API 課金トークンを抑制。

---

## 4. コスト最適化（マルチエージェント運用規律）

1. **Gemini 3.1 Flash の適材適所利用**:
   - 簡易なテキストパース、依存パッケージのドリフト確認などには安価な `Gemini Flash` を使用し、料金が10倍高い `Gemini Pro` は構造分析や社長プレゼン準備 (T658等) にのみ割り当てる。
2. **プロンプトキャッシュの積極活用**:
   - 26件の docs/*.md をコンテキストに載せて NotebookLM やエージェントを回す際、キャッシュを活用して入力トークン料金を **最大 90% 削減** する (T691PoC検証予定)。
