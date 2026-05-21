# Google Workspace 移行・共有作業手順書

作成日: 2026-05-21  
対象プロジェクト: Mighty-Link AI Connect / Mighty Skill-Bridge

## 目的

Mighty Skill-Bridge の Google API 実行主体を、新しい Google Workspace アカウント `k-umezawa@ml-mightylink.com` に移行し、WBS カレンダー、進捗管理スプレッドシート、ローカル FastAPI サーバーの連携を同一アカウントで運用できる状態にする。

## 関係アカウントとリソース

- Workspace 実行アカウント: `k-umezawa@ml-mightylink.com`
- Google Cloud Console 管理側アカウント: `kanta13jp@gmail.com`
- 共有先: `kobayashi-masami@ml-mightylink.com`
- Google Cloud プロジェクト: `mighty-link-ai-connect`
- カレンダー名: `Mighty Skill-Bridge 開発計画`
- 進捗管理スプレッドシート ID: `1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8`
- OAuth トークン: `authorized_user.json`

## 実施済み作業

### 1. Google OAuth テストユーザー登録

新しい Workspace アカウントで OAuth 認証を開始したところ、Google OAuth アプリがテストモードのため、未登録ユーザーとしてブロックされた。

対応手順:

1. `kanta13jp@gmail.com` で Google Cloud Console にログイン。
2. プロジェクト `mighty-link-ai-connect` を選択。
3. Google Auth Platform の対象または OAuth 同意画面を開く。
4. テストユーザーに `k-umezawa@ml-mightylink.com` を追加。
5. 保存後、OAuth 認証を再実行。

結果: `k-umezawa@ml-mightylink.com` で OAuth 認証が通る状態になった。

### 2. WBS カレンダー同期

実行コマンド:

```powershell
python scripts/sync_wbs_to_calendar.py
```

実施内容:

- ブラウザ認証で `k-umezawa@ml-mightylink.com` を選択。
- Google Calendar / Sheets / Drive の権限を許可。
- `authorized_user.json` を新しい Workspace アカウント用に更新。
- `Mighty Skill-Bridge 開発計画` カレンダーを作成。
- WBS 開発スケジュール全 6 件を同期。
- `exports/mighty_development_plan.ics` を生成。

結果: Calendar sync は `Success: 6, Failed: 0` で完了。

### 3. スプレッドシートアクセス権の解消

`share_resources.py` 実行時に、以下の 404 が発生した。

```text
File not found: 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
```

原因: 対象スプレッドシートが旧アカウント側の Drive にあり、`k-umezawa@ml-mightylink.com` に編集権限がなかった。

対応手順:

1. スプレッドシートのオーナー権限を持つアカウントで対象 Sheets を開く。
2. 右上の共有から `k-umezawa@ml-mightylink.com` を追加。
3. 権限を編集者に設定して保存。

結果: Workspace 実行アカウントから対象 Sheets を開けるようになった。

### 4. 小林社長への自動共有

実行コマンド:

```powershell
python scripts/share_resources.py
```

実施内容:

- `Mighty Skill-Bridge 開発計画` カレンダーを `kobayashi-masami@ml-mightylink.com` に `writer` 権限で共有。
- 進捗管理スプレッドシートを同じく `writer` 権限で共有。

結果: カレンダーと Sheets の共有が完了。

### 5. FastAPI サーバー再起動

実行コマンド:

```powershell
python src/app.py
```

確認内容:

- `http://localhost:8000` で画面が表示される。
- `src/index.html` が UTF-8 として読み込まれる。
- Sheets 連携はプロジェクトルートの `client_secret.json` / `authorized_user.json` を利用する。

## 再実行チェックリスト

- `client_secret.json` がプロジェクトルート直下にある。
- `authorized_user.json` が `k-umezawa@ml-mightylink.com` の認証情報で更新されている。
- Google Cloud Console のテストユーザーに `k-umezawa@ml-mightylink.com` が含まれている。
- 対象スプレッドシートが `k-umezawa@ml-mightylink.com` に編集者共有されている。
- `python scripts/sync_wbs_to_calendar.py` が成功する。
- `python scripts/share_resources.py` が成功する。
- `http://localhost:8000` が表示される。

## 運用メモ

- 認証ファイルは Git 管理対象外。共有やコミットは行わない。
- スクリプトはどの作業ディレクトリからでもルートの認証ファイルを参照できるよう、プロジェクトルート基準のパス解決にしている。
- WBS の編集元は [data/WBS.tsv](../data/WBS.tsv)。カレンダー同期の `.ics` 出力先は [exports/mighty_development_plan.ics](../exports/mighty_development_plan.ics)。
