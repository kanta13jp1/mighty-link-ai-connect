# Firebase CI/CD WIF移行 ＆ レガシーTOKEN廃止レポート

作成日: 2026-07-08  
関連WBS: T852  
関連課題: R100  
関連QA: QA-77  

## 1. 概要

GitHub Actions上の本番デプロイパイプライン（`CI/CD Pipeline`）において、セキュリティリスクの高い永続的な `FIREBASE_TOKEN`（レガシーToken）の依存を完全に排除し、Workload Identity Federation (WIF) および Application Default Credentials (ADC) を用いたセキュアな認証構造への移行を完了しました。

## 2. 移行対応内容

### (1) ワークフローファイルの修正（[.github/workflows/deploy.yml](../.github/workflows/deploy.yml)）
- デプロイの環境変数（`env`）から `FIREBASE_TOKEN` シークレットの読み込みを完全に削除しました。
- デプロイ実行スクリプトから、旧 `FIREBASE_TOKEN` による認証フォールバック処理（`--token` 指定）をすべて削除し、WIF/ADC によるGoogle Cloudの認証ファイル（`GOOGLE_APPLICATION_CREDENTIALS`）経由のみで `firebase deploy` が動作するコード構成に一本化しました。

### (2) 認証経路の正常性検証
- `google-github-actions/auth@v3` を用いた Workload Identity 経由のトークン取得が正常に動作し、Firebase CLI が環境変数 `GOOGLE_APPLICATION_CREDENTIALS` を介して正規のサービスアカウント権限で本番Firebase Hostingプロジェクト (`mighty-link-ai-connect-13d22`) へアクセスできることを確認しました。

## 3. 移行効果とセキュリティ向上点

1. **長期持続トークンの廃止**: 漏洩時に永続的なプロジェクト変更権限を与える `FIREBASE_TOKEN` が完全に廃止され、GitHub Actions側でのシークレット漏洩リスクが極小化されました。
2. **短寿命アクセスキーの使用**: デプロイの都度、Google Cloud上のWorkload Identityプールを介して動的に短寿命のOAuthトークンが発行されるため、認証セキュリティが最新の業界標準レベルに強化されました。
3. **明示的なエラーハンドリング**: 認証ファイルが見つからない、またはWIFでの接続に失敗した場合は直ちにデプロイプロセスがエラー終了するようになり、意図しない認証状態でのデプロイ混入が防止されます。
