# Mighty Skill-Bridge：デモ環境セキュリティおよび認証・アクセス制限設計書

**作成日**: 2026年6月3日（2026年7月23日現行化）  
**ステータス**: 運用中  
**対象フェーズ**: 7. 次期開発・運用（セキュリティ）  
**関連タスク**: **T686** 認証設計、**T913** ログイン必須化、**T915** 静的配信バイパス解消  
**関連Issue/課題**: [R10](../data/issues_tracker.tsv#L11) (公開URLの外部漏洩対策)

---

## 1. 背景とセキュリティ要件
本システム（Mighty Skill-Bridge）は、実在する経歴書や求人案件データを扱うため、インターネット上に公開されるデモ環境（Firebase Hosting 上）には第三者による無断アクセスを防止するための強固な認証層（アクセス制限）が必須となります。

本設計書では、**Firebase Hosting + Cloud Functions (FastAPI)** という現行インフラアーキテクチャ特性を踏まえ、追加コストを発生させず（初期費用・月額 $0）、最もシンプルかつ確実に全画面・全APIを保護するためのアクセス制御手段を設計・比較します。

---

## 2. アクセス制限の方式比較

デモ環境の保護において検討される以下の3つのアプローチを比較評価します。

| 方式 | 概要 | 費用 | 実装難易度 | 推奨度 |
| :--- | :--- | :--- | :--- | :--- |
| **A. 全リクエストのCloud Functions集約によるBasic Auth保護 (推奨)** | Firebase Hosting のルーティング（`firebase.json`）で静的ファイル（`index.html`）を含むすべてのパス（`/**`）を FastAPI サーバー（Functions）へリライトし、FastAPI 内のセキュリティ依存関係（`HTTPBasic`）で一括認証します。 | **$0** (無料枠内) | 低〜中 | ⭐️⭐️⭐️⭐️⭐️ (最推奨) |
| **B. Cloudflare Workersを用いたエッジでのBasic Auth適用** | ドメインのネームサーバーを Cloudflare に変更し、エッジサーバー（Workers）でBasic Auth認証ヘッダーを検証した上で Firebase Hosting へ転送します。 | **$0** (Workers無料枠) | 中 (DNS操作が必要) | ⭐️⭐️⭐️ (ドメイン移管時のみ) |
| **C. Google Cloud Identity-Aware Proxy (IAP) の導入** | ホスティング先を Firebase から Cloud Run へ移行し、GCPのIAP（ID認識型プロキシ）を有効化して、GoogleアカウントによるSSOを強制します。 | **$0.00** | 高 (IAM管理が必要) | ⭐️⭐️ (大企業・社内専用向け) |

### 結論：
開発スピード、追加の外部サービス依存（DNS操作等）の回避、およびランニングコスト $0 を維持するため、**「方式A：全リクエストのCloud Functions集約によるBasic Auth保護」** を採用します。

---

## 3. 方式A：詳細設計

### 3.1 ルーティング設計（firebase.json）
Firebase Hosting は、リライトより完全一致の静的ファイルを優先します。したがって `public: "."` のまま全パスリライトを追加しても、`/` と `/index.html` は配置済みの `index.html` を直接返し、FastAPI の認証へ到達しません。

`public` は実質空の専用ディレクトリへ分離し、アプリケーションHTMLやプロジェクトデータを一切配置しません。`firebase-hosting/.gitkeep` は `**/.*` の ignore 規則によりデプロイ対象外です。静的完全一致が存在しない状態で、最後の `**` リライトが全リクエストを `api` サービスへ集約します。

```json
{
  "hosting": {
    "public": "firebase-hosting",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**",
      "venv/**",
      "tests/**",
      ".git/**",
      ".github/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "run": {
          "serviceId": "api",
          "region": "us-central1"
        }
      }
    ]
  }
}
```

### 3.2 FastAPI (Python) での認証実装設計
FastAPI の管理ランタイム用ミドルウェアで、死活監視用の `/api/health` を除く全画面・全APIへ HTTP Basic 認証を適用します。未認証リクエストは `WWW-Authenticate: Basic` を伴うHTTP 401となり、HTML・業務API本文を返しません。個別ルートの認証依存関係も多層防御として維持します。

* **セキュリティスキーマ**: `fastapi.security.HTTPBasic` を使用。
* **認証情報の取得**: 環境変数 `BASIC_AUTH_USERNAME` および `BASIC_AUTH_PASSWORD` を参照。
* **fail-closed**: 管理ランタイム・ローカル実行とも既知の開発用デフォルト値を持ちません。管理ランタイムで認証情報が欠けた場合、全保護ルートをHTTP 503で閉鎖します。
* **シークレット分離**: GitHub Actions の `BASIC_AUTH_USERNAME` / `BASIC_AUTH_PASSWORD` 専用SecretsをFirebase Functionsの`.env`へデプロイ時に上書きし、欠落または最小長未満ならデプロイを停止します。
* **キャッシュ制御**: 認証後の応答へ `Cache-Control: private, no-store, max-age=0` を付与します。

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
import os
import secrets

is_managed_runtime = bool(os.environ.get("K_SERVICE") or os.environ.get("FUNCTION_TARGET"))
username = os.environ.get("BASIC_AUTH_USERNAME")
password = os.environ.get("BASIC_AUTH_PASSWORD")

@app.middleware("http")
async def enforce_managed_runtime_authentication(request: Request, call_next):
    if not is_managed_runtime or request.url.path == "/api/health":
        return await call_next(request)
    if not username or not password:
        return JSONResponse(status_code=503, content={"detail": "Site authentication is not configured"})
    # Authorizationヘッダーを復号し、UTF-8 bytesへ変換して
    # secrets.compare_digest()でユーザー名・パスワードを比較する。
    ...
```

### 3.3 IP制限の併用設計（将来的な拡張）
社長からの要望、またはパイロットユーザーのオフィスIPアドレスが確定した場合、FastAPI のミドルウェア層で IP アドレスのホワイトリストチェックを追加できます。

* **実装箇所**: FastAPI の `BaseHTTPMiddleware` を継承したカスタムミドルウェア。
* **IP 判定**: `request.client.host`、またはリバースプロキシ（Firebase CDN）経由の場合は `X-Forwarded-For` ヘッダーからクライアントIPを抽出し、指定のホワイトリストと比較。
* **フォールバック**: IPアドレスがホワイトリストにない場合でも、Basic Auth 認証をパスすればアクセス可能とする「ハイブリッド制限」にすることで、モバイル端末からの接続柔軟性を担保します。

---

## 4. 運用・管理ルール

1. **認証情報のローテーション**:
   * パイロットユーザーが変更されるたび、GitHub Actions専用Secretsの `BASIC_AUTH_USERNAME` / `BASIC_AUTH_PASSWORD` を更新し、GitHub Actions経由で再デプロイを実施します。値はリポジトリ・Workflowログ・報告書へ記載しません。
2. **監査ログでのアクセス確認**:
   * HTTPステータスとアクセス元情報はCloud Run / Cloud Functionsのリクエストログで確認します。アプリケーションはBasic Authの実値を記録しません。認証失敗専用イベントの長期保存は未実装であり、必要時は秘密値を含めない構造化ログとして別途実装します。
3. **継続検証**:
   * `tests/test_firebase_hosting_auth_gate.py` が `public` 直下への通常ファイル混入と全パスリライト欠落を検知します。
   * `tests/test_auth_security.py` が未認証401、認証済み200、全業務APIの管理ランタイム認証、設定欠落503、既知資格情報の非埋め込み、`no-store` を検証します。
   * 本番反映後は `https://mightylink-app.com/` と業務APIが未認証で401を返し、`/api/health` だけが未認証200を返すことを外形確認します。
