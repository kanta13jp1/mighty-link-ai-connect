# Mighty Skill-Bridge：デモ環境セキュリティおよび認証・アクセス制限設計書（T686）

**作成日**: 2026年6月3日  
**ステータス**: 完了  
**対象フェーズ**: 7. 次期開発・運用（セキュリティ）  
**関連タスク**: **T686** デモ環境へのbasic authまたはIP制限の導入設計  
**関連Issue/課題**: [R10](file:///c:/Users/kanta/GitHub/mighty-link-ai-connect/data/issues_tracker.tsv#L11) (公開URLの外部漏洩対策)

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
現在、`firebase.json` は `/api/**` および `/admin/**` のみを Cloud Functions へ流していますが、静的ファイル `index.html` の直アクセスも保護するため、以下のようにすべてのリクエスト（`/**`）を `api` 関数へ書き換えます。

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**",
      "venv/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "function": "api"
      }
    ]
  }
}
```

### 3.2 FastAPI (Python) での認証実装設計
FastAPI 内で、静的ファイルを配信する `StaticFiles` マウントおよびルート `/` の手前に、認証依存関係を追加します。

* **セキュリティスキーマ**: `fastapi.security.HTTPBasic` を使用。
* **認証認証情報の取得**: 環境変数 `BASIC_AUTH_USERNAME` および `BASIC_AUTH_PASSWORD` を参照。設定がない場合はデフォルトの認証情報をフォールバックとして使用。

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

security = HTTPBasic()

def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.environ.get("BASIC_AUTH_USERNAME", "mighty")
    correct_password = os.environ.get("BASIC_AUTH_PASSWORD", "link2026")
    
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ルートURL (/) にアクセスされた場合、Basic Auth認証後に index.html を返す
@app.get("/")
def read_root(username: str = Depends(verify_basic_auth)):
    return FileResponse("index.html")

# exports などの静的フォルダも Basic Auth の配下に置く
class AuthenticatedStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send):
        # 認証をフックする処理 (FastAPI のミドルウェアまたはルートレベルで検証)
        pass
```

### 3.3 IP制限の併用設計（将来的な拡張）
社長からの要望、またはパイロットユーザーのオフィスIPアドレスが確定した場合、FastAPI のミドルウェア層で IP アドレスのホワイトリストチェックを追加できます。

* **実装箇所**: FastAPI の `BaseHTTPMiddleware` を継承したカスタムミドルウェア。
* **IP 判定**: `request.client.host`、またはリバースプロキシ（Firebase CDN）経由の場合は `X-Forwarded-For` ヘッダーからクライアントIPを抽出し、指定のホワイトリストと比較。
* **フォールバック**: IPアドレスがホワイトリストにない場合でも、Basic Auth 認証をパスすればアクセス可能とする「ハイブリッド制限」にすることで、モバイル端末からの接続柔軟性を担保します。

---

## 4. 運用・管理ルール

1. **認証情報のローテーション**:
   * パイロットユーザーが変更されるたび、環境変数 `BASIC_AUTH_PASSWORD` を変更し、GitHub Actions経由で再デプロイを実施します。
2. **監査ログでの認証試行記録**:
   * 認証の成否、およびアクセス元のIPアドレスは、監査ログ（`data/audit/`）に自動記録され、不正アクセス試行の早期検出に使用されます。
