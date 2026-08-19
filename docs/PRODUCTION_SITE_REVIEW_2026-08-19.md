# 本番サイト総合レビュー 2026-08-19

## 対象

- URL: https://mightylink-app.com/
- 最終アプリケーションコミット: `f69e9d02`
- 範囲: 認証境界、主要業務API、レスポンシブ表示、主要操作、ブラウザエラー、HTTPセキュリティヘッダー、CI/CD

## 検出事項と是正

| 優先度 | 検出事項 | 是正結果 |
| :-- | :-- | :-- |
| Critical | トップ画面だけがBasic Authで保護され、案件・エンジニア・営業メール照合等の業務APIは未認証で200を返していた | 管理ランタイムでは`/api/health`以外の全ルートを共通ミドルウェアで保護。未設定時は503でfail-closedとした |
| Critical | リポジトリで既知の初期Basic Auth資格情報が本番で利用可能だった | 初期値とコード内フォールバックを撤去し、暗号学的乱数で資格情報をローテーション。GitHub Actions専用Secretsを必須化した |
| High | Basic Auth通過後にも任意値を受け付けるクライアント側ログイン画面が表示された | サーバー認証済みマーカーを導入し、本番では重複ログインを表示しないようにした |
| High | 1440pxと390pxの両方で横方向のはみ出しがあり、モバイルではサイドバーが本文を画面外へ押し出した | グリッド、サイドバー、比較セレクト、トップバー、入力欄をレスポンシブ化した |
| Medium | Cloud Runへのリライト後の401応答にCSP、HSTS等のセキュリティヘッダーが付かなかった | FastAPIの全応答へ6種のブラウザ防御ヘッダーを付与し、401・200・ヘルスチェックで回帰テストを追加した |

## 本番検証結果

| 確認項目 | 結果 |
| :-- | :-- |
| 未認証 `/`、`/api/jobs`、`/api/engineers`、`/api/sales-email/matches`、`/api/onboarding/state` | すべて401 |
| 認証済み同5ルート | すべて200 |
| 未認証 `/api/health` | 200 |
| 旧資格情報・無効資格情報 | 401 |
| CSP / HSTS / nosniff / frame guard / referrer policy / permissions policy | 付与済み |
| 1440x900 | 横スクロールなし、分析実行成功、コンソールエラー0件 |
| 390x844 | 横スクロールなし、本文が先頭表示、1列入力、メニュー開閉成功、コンソールエラー0件 |
| 外部疑似ペネトレーション診断 | HIGH 0、MED 1、LOW 0。残るMED 1は意図した未認証401の機械判定 |

画面証跡: [デスクトップ](../exports/production_review/desktop.png)、[分析結果](../exports/production_review/desktop_analysis.png)、[モバイル](../exports/production_review/mobile.png)。検査結果は [UI監査JSON](../exports/production_review/ui_audit.json)、[外部診断レポート](../exports/production_review/pentest.md)、[外部診断JSON](../exports/production_review/pentest.json) に保存した。

## 品質ゲートとデプロイ

- ローカル完全プリフライト: ガード29/29、テスト909件、失敗0、エラー0
- レスポンシブ修正デプロイ: `fce3a3ac` / GitHub Actions `32258769483` 成功
- セキュリティヘッダー修正デプロイ: `f69e9d02` / GitHub Actions `32260637963` 成功
- `python scripts/verify_public_demo.py --url https://mightylink-app.com/`: PASS

## 運用上の注意

- 現在の資格情報はローカル`.env`とGitHub Actions Secretsで管理し、文書・ログ・Git履歴へ値を残さない。
- Google Sheets / CalendarへのWBS同期はOAuth再認証が必要なため、このレビューの本番サイト合否とは分離して扱う。
