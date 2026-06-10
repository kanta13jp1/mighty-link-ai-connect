# システム監査ログ 氏名マスキング・暗号化パイプライン設計書 (T756)

個人情報保護法（改正2022年）・GDPR Article 32 に基づき、**Mighty Skill-Bridge** のシステム監査ログに含まれる個人識別情報（PII）を安全に処理するパイプラインを定義します。

---

## バージョン履歴

| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-10 | v1.0.0 | 初版作成（マスキング方針・暗号化設計・バッチ実装仕様） | Claude Code |

---

## 1. 対象ログとPII分類

| ログ種別 | 格納先 | PII フィールド | マスキング方針 |
| :--- | :--- | :--- | :--- |
| Firebase Auth アクセスログ | Google Cloud Logging | メールアドレス・IPアドレス | 部分マスク + 保持期間30日 |
| Cloud Functions 実行ログ | Google Cloud Logging | firebase_uid・メール・氏名 | SHA-256 ハッシュ化（一方向） |
| Supabase `audits` テーブル | PostgreSQL | prompt内容（氏名含む可能性） | AES-256-GCM 暗号化 |
| Supabase `profiles` 変更履歴 | PostgreSQL row-level audit | 氏名・メールアドレス | AES-256-GCM 暗号化 |
| アプリケーションログ（FastAPI） | Stdout → Cloud Logging | 氏名・経歴書テキスト | 正規表現マスキング |

---

## 2. マスキング方針

### 2.1 メールアドレスの部分マスク

```
元: kanta@example.com
マスク後: k***@e***.com
```

### 2.2 氏名のマスク

```
元: 梅澤 寛太
マスク後: 梅* **
```

### 2.3 firebase_uid の一方向ハッシュ（Cloud Logging 用）

ログの関連付けを保ちつつ元の UID を秘匿するため、HMAC-SHA256 を使用する。

```python
import hmac, hashlib, os

def pseudonymize_uid(firebase_uid: str) -> str:
    """監査ログ用 UID の仮名化（HMAC-SHA256）"""
    secret = os.environ["LOG_PSEUDONYM_SECRET"].encode()
    return hmac.new(secret, firebase_uid.encode(), hashlib.sha256).hexdigest()[:16]
```

- `LOG_PSEUDONYM_SECRET` は GCP Secret Manager に格納し、Cloud Functions 実行時に注入する。
- 同一 UID は常に同一ハッシュになるため、ログ間の相関追跡が可能。

---

## 3. 暗号化設計（Supabase audits テーブル）

### 3.1 暗号化アルゴリズム

| 項目 | 選択 | 理由 |
| :--- | :--- | :--- |
| アルゴリズム | AES-256-GCM | 認証付き暗号化・NIST推奨 |
| 鍵長 | 256 bit | GDPR / 個人情報保護法 の「適切な安全管理措置」を満たす |
| 鍵管理 | GCP Secret Manager | ローテーション・監査ログ対応 |
| IV (初期化ベクタ) | 96 bit ランダム（暗号文に付加） | GCM 標準推奨 |

### 3.2 暗号化対象フィールド

```sql
-- audits テーブルの暗号化対象カラム
-- prompt_text: Gemini API に送信したプロンプト（氏名・経歴を含む可能性あり）
-- response_text: Gemini API のレスポンス本文

ALTER TABLE public.audits
  ADD COLUMN IF NOT EXISTS prompt_text_enc  BYTEA,  -- AES-256-GCM 暗号文
  ADD COLUMN IF NOT EXISTS response_text_enc BYTEA; -- AES-256-GCM 暗号文
```

### 3.3 Python 暗号化ユーティリティ

```python
# functions/utils/crypto.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64

def encrypt_pii(plaintext: str, key_bytes: bytes) -> str:
    """AES-256-GCM で暗号化し、base64(nonce + ciphertext) を返す"""
    aesgcm = AESGCM(key_bytes)
    nonce = os.urandom(12)  # 96-bit IV
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()

def decrypt_pii(b64_enc: str, key_bytes: bytes) -> str:
    """base64(nonce + ciphertext) を復号して平文を返す"""
    raw = base64.b64decode(b64_enc)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key_bytes)
    return aesgcm.decrypt(nonce, ct, None).decode()
```

---

## 4. アプリケーションログ マスキングミドルウェア

FastAPI のログに氏名・メールが混入しないよう、`logging` フィルタで自動マスクする。

```python
# functions/utils/log_filter.py
import logging, re

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
NAME_RE  = re.compile(r'[぀-ヿ一-鿿]{2,4}\s[぀-ヿ一-鿿]{1,4}')

class PIIRedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        msg = EMAIL_RE.sub('[EMAIL]', msg)
        msg = NAME_RE.sub('[NAME]', msg)
        record.msg = msg
        record.args = ()
        return True

# main.py (FastAPI エントリポイント) で登録
import logging
logging.getLogger().addFilter(PIIRedactFilter())
```

---

## 5. Cloud Logging 保持ポリシー設定

| ログバケット | 保持期間 | 理由 |
| :--- | :--- | :--- |
| `_Default` (全サービス) | 30日 | GDPRの「必要最小限の保持」原則 |
| `_Required` (監査ログ) | 400日 | GCP 規定の最低保持期間（変更不可） |
| アプリケーションログ（カスタム） | 90日 | 不正アクセス調査のための最小保持 |

```bash
# Cloud Logging 保持ポリシー設定（gcloud CLI）
gcloud logging buckets update _Default \
  --location=global \
  --retention-days=30
```

---

## 6. 鍵ローテーション手順

1. **GCP Secret Manager** で新バージョンの鍵を追加（`AUDIT_ENCRYPTION_KEY_v2`）
2. Cloud Functions の環境変数 `AUDIT_ENCRYPTION_KEY` を新鍵に更新してデプロイ
3. 既存の暗号化済みレコードを新鍵で再暗号化するバッチを実行（`scripts/reencrypt_audit_logs.py`）
4. 旧鍵バージョンを GCP Secret Manager で無効化

ローテーション頻度：**年1回**（T751 の API キーローテーション運用と合わせて実施）

---

## 7. テスト要件

| テストケース | 期待結果 |
| :--- | :--- |
| `encrypt_pii` → `decrypt_pii` のラウンドトリップ | 元の平文が復元される |
| Cloud Functions ログに実メールが含まれない | `[EMAIL]` に置換されている |
| Cloud Functions ログに日本語氏名が含まれない | `[NAME]` に置換されている |
| 異なる IV で同一平文を暗号化 | 毎回異なる暗号文になる |
| 不正な鍵で復号 | `cryptography.exceptions.InvalidTag` が発生 |

---

## 8. 関連ドキュメント

- [Firebase / Supabase システムアーキテクチャ詳細設計書](FIREBASE_SUPABASE_SYSTEM_ARCHITECTURE.md)
- [ユーザーデータ完全消去フロー設計書](USER_DATA_DELETION_FLOW.md)
- [災害復旧・エスカレーション連絡網ランブック](DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md)
