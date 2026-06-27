# 利用規約・プライバシーポリシー同意UI/API Runbook (T745)

> 最終更新: 2026-06-27
> 関連WBS: T745 / T777 / T798 / T752 / T845
> 関連Go/No-Go: PUBLIC-05 / PUBLIC-07
> 関連課題・QA: R102 / QA-82

---

## 1. 目的

Mighty Skill-Bridge のAI診断・案件マッチング実行前に、利用者が次の法定・規約ドラフトを確認したことをUIとAPIの両方で検証する。

- [サービス利用規約](TERMS_OF_SERVICE.md)
- [プライバシーポリシー](PRIVACY_POLICY.md)
- [特定商取引法に基づく表記](TOKUSHOHO_NOTATION.md)
- [課金規約・返金ポリシー](BILLING_AND_REFUND_POLICY.md)

このRunbookの完了により、WBS T745「サービス利用規約およびプライバシーポリシー本番UIでの同意チェックボックス実装」は完了扱いとする。ただし、本文は引き続きドラフトであり、T798の法務確認とT804の価格確定が完了するまで一般公開・有償ローンチはNo-Goである。

---

## 2. 現行同意バージョン

| 項目 | 値 |
| --- | --- |
| 同意バージョン | `MSB-LEGAL-2026-06-DRAFT` |
| UI対象 | `index.html`, `src/index.html` |
| API対象 | `POST /api/parse`, `POST /api/match` |
| 検証関数 | `src/app.py::validate_legal_consent` |
| テスト | `tests/test_api.py`, `tests/test_legal_consent_ui.py` |

バージョン値は、将来T798で確定版へ差し替える際に変更する。旧バージョンを送ったクライアントは400で拒否されるため、規約改定時にUIとAPIを同時に更新できる。

---

## 3. UI要件

公開デモのAnalyzeボタン直前に、法定・規約ドラフトへの同意チェックボックスを配置する。

- チェック未選択では `runAnalysis()` がAPI送信前に停止する。
- 画面上に、法務確認・価格確定前のドラフト版であることを表示する。
- 同意対象の4ドキュメントへ直接リンクする。
- フッターにも「法定・規約」列を追加し、4ドキュメントへ常時リンクする。

GitHub Pagesのcontrolled demoでも同じUIを表示する。GitHub Pagesは静的ミラーであり、実API保存や本番課金導線の許可を意味しない。

---

## 4. API契約

### `POST /api/parse`

multipart/form-data に次のフィールドを含める。

```text
legal_consent_accepted=true
legal_consent_version=MSB-LEGAL-2026-06-DRAFT
```

### `POST /api/match`

JSON body に次のフィールドを含める。

```json
{
  "legal_consent_accepted": true,
  "legal_consent_version": "MSB-LEGAL-2026-06-DRAFT"
}
```

### 失敗時

| 条件 | HTTP | detail |
| --- | --- | --- |
| 同意未取得 | 400 | `Terms of Service and Privacy Policy consent is required before running this API.` |
| バージョン不一致 | 400 | `Invalid legal consent version. Expected MSB-LEGAL-2026-06-DRAFT.` |

### 成功時

レスポンスに次のメタデータを含める。

```json
{
  "legal_consent": {
    "accepted": true,
    "version": "MSB-LEGAL-2026-06-DRAFT",
    "source": "api_match",
    "docs": [
      "TERMS_OF_SERVICE.md",
      "PRIVACY_POLICY.md",
      "TOKUSHOHO_NOTATION.md",
      "BILLING_AND_REFUND_POLICY.md"
    ]
  }
}
```

---

## 5. 今回の完了範囲

- `index.html` / `src/index.html` に同意チェックボックス、同意ステータス、法定・規約フッターリンクを追加。
- `src/app.py` に `LEGAL_CONSENT_VERSION`、対象ドキュメント一覧、`validate_legal_consent()` を追加。
- `/api/parse` と `/api/match` で同意必須・バージョン一致を検証。
- 成功レスポンスに同意メタデータを返却。
- `tests/test_api.py` で未同意・旧バージョン拒否と成功時メタデータを検証。
- `tests/test_legal_consent_ui.py` でUIリンク、チェックボックス、JS payload、フッター常時リンクを静的検証。
- PUBLIC-05 と PUBLIC-07 を実装ゲートとしてPASSへ更新。

---

## 6. 残ゲート

T745完了後も、次の理由により `public_paid_launch` はNo-Goのまま維持する。

- T798: 利用規約・プライバシーポリシー・特商法表記・課金規約の法務確認と本文確定。
- T804: 料金プラン、販売価格、返金条件のCEO承認。
- T752: Firebase Auth / 所有者スコープに紐づく正式なユーザー登録・同意履歴保存。
- T770 / T776 / T791 / T807: 課金、負荷、Stripe live、Webhook、請求停止・返金の本番検証。
- T817_7: 営業メールAIマッチングの本番運用、個人情報、監査、負荷確認。
- T845 / T849 / T850 / T852 / T854: 全機能UAT、サイト開発完了総合判定、会社運用引継ぎ、Firebase CI/CD、課題/QA棚卸し。

---

## 7. 公式ドキュメント確認メモ

2026-06-27のT745完了時に、次の公式ドキュメントを確認した。

- OpenAI Codex manual: `C:\Users\kanta\AppData\Local\Temp\openai-docs-cache\codex-manual.md`
- Anthropic Claude Code Docs: https://code.claude.com/docs/en/overview
- Google Workspace Sheets API batchUpdate: https://developers.google.com/workspace/sheets/api/guides/batchupdate
- Firebase Hosting: https://firebase.google.com/docs/hosting
- GitHub Actions Docs: https://docs.github.com/actions
- Supabase Docs: https://supabase.com/docs
- Stripe Docs: https://docs.stripe.com/
- 消費者庁 特定商取引法関連情報: https://www.caa.go.jp/policies/policy/consumer_transaction/specified_commercial_transactions/

---

## 8. 運用メモ

- 法務確定前のドラフト同意であることを、UI、Runbook、Go/No-Goに明記する。
- 規約本文の実値、事業者情報、価格、返金条件はT798/T804の確定結果で更新する。
- ユーザー別の永続的な同意履歴はT752の正式アカウント基盤で実装する。現T745は診断/マッチング実行時のAPIガードである。
- OAuth token、secret、個人データ実値、営業メール本文全文はGitHub、Sheets、docs、NotebookLMへ記録しない。
