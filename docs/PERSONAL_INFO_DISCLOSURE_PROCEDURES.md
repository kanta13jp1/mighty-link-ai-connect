# 第三者提供記録・開示請求対応手順書 (T765)

個人情報保護法第25条（第三者提供記録義務）・第32〜36条（開示・訂正・削除・利用停止請求）に基づき、**Mighty Skill-Bridge** における個人情報関連の請求対応手順を定義します。

---

## バージョン履歴

| 日付 | バージョン | 内容 | 起稿者 |
| :--- | :--- | :--- | :--- |
| 2026-06-10 | v1.0.0 | 初版作成（第三者提供記録・4種請求対応・SLA定義） | Claude Code |

---

## 1. 第三者提供記録（法第25条）

### 1.1 外部サービスへの個人情報提供一覧

| 提供先 | 提供データ | 目的 | 根拠 | 保護措置 |
| :--- | :--- | :--- | :--- | :--- |
| Google (Gemini API) | 経歴書テキスト・案件情報（氏名は含まない） | AI診断処理 | 業務委託（法25条適用外） | Google Cloud DPA 締結・データ処理地域: 日本 |
| Google (Firebase / GCP) | firebase_uid・メールアドレス | 認証・ホスティング | 業務委託 | Google Cloud DPA・SOC2 Type II 認証取得済 |
| Supabase | 全ユーザーデータ | DB ホスティング | 業務委託 | Supabase DPA・GDPR 準拠・EU 標準契約条項(SCC) |

> **注**: 業務委託先（Gemini API / Firebase / Supabase）は第三者提供には該当しないが、委託先管理として DPA（Data Processing Agreement）の締結を維持する。

### 1.2 第三者提供記録台帳

第三者への提供が発生した場合は `data/third_party_provision_log.tsv` に記録する。

```
提供日	提供先名称	提供データ種別	提供目的	本人同意日	同意方法	記録者
```

現時点での第三者提供実績：**なし**（業務委託先のみ）

---

## 2. 開示請求対応（法第32条）

### 2.1 受付手順

```
1. ユーザーから書面・メールで開示請求を受理
   受付先: k-umezawa@ml-mightylink.com
   件名形式: 「【個人情報開示請求】{氏名}」

2. 本人確認
   - メールアドレス + 登録時の氏名で照合
   - 必要に応じて追加確認（登録日・最終ログイン日等）

3. 対象データの抽出（Supabase ダッシュボード）
```

```sql
-- 開示対象データの全件抽出
SELECT
  p.user_id,
  p.name,
  p.email,
  p.resume_profile,
  p.created_at,
  p.updated_at,
  json_agg(json_build_object(
    'project_id', m.project_id,
    'fit_score', m.fit_score,
    'matched_skills', m.matched_skills,
    'missing_skills', m.missing_skills,
    'created_at', m.created_at
  )) AS matches
FROM public.profiles p
LEFT JOIN public.matches m ON m.user_id = p.user_id
WHERE p.user_id = '<firebase_uid>'
GROUP BY p.user_id, p.name, p.email, p.resume_profile, p.created_at, p.updated_at;
```

```
4. CSV / JSON でエクスポートし、パスワード付き ZIP で本人にメール送付
5. 対応完了を data/disclosure_request_log.tsv に記録
6. SLA: 受付後 2 週間以内に開示
```

---

## 3. 訂正請求対応（法第34条）

### 3.1 手順

```
1. 訂正内容・根拠を確認（本人の申し出 + 証拠書類）
2. Supabase ダッシュボードで直接更新（管理者権限）
```

```sql
-- profiles テーブルの訂正（例: 氏名変更）
UPDATE public.profiles
SET
  name = '<新しい氏名>',
  updated_at = NOW()
WHERE user_id = '<firebase_uid>';
```

```
3. 訂正結果を本人にメールで通知
4. data/correction_request_log.tsv に記録
5. SLA: 受付後 2 週間以内に訂正完了
```

---

## 4. 削除請求対応（法第35条 / GDPR Article 17）

退会フロー（`DELETE /api/v1/users/me`）を管理者が代理実行する。

```bash
# 管理者が代理で削除 API を呼び出す場合
# 対象ユーザーの firebase_uid を取得後、Service Role Key で直接実行

python scripts/admin_delete_user.py --firebase-uid <uid>
```

詳細手順は [ユーザーデータ完全消去フロー設計書](USER_DATA_DELETION_FLOW.md) を参照。

SLA: **受付後 2 週間以内**（GDPR では 30 日以内）

---

## 5. 利用停止請求対応（法第37条）

```
1. Firebase Authentication ダッシュボードでアカウントを無効化
   Authentication → Users → 該当ユーザー → 「アカウントを無効にする」

2. Supabase RLS により disabled ユーザーはデータにアクセス不能になる
   （firebase_uid の JWT が発行されなくなるため）

3. 本人に無効化完了をメールで通知
4. data/suspension_request_log.tsv に記録
5. SLA: 受付後 3 営業日以内
```

---

## 6. 対応記録台帳の管理

### 6.1 台帳ファイル一覧

| ファイル | 内容 | 保持期間 |
| :--- | :--- | :--- |
| `data/disclosure_request_log.tsv` | 開示請求受付・対応記録 | 5年 |
| `data/correction_request_log.tsv` | 訂正請求受付・対応記録 | 5年 |
| `data/deletion_request_log.tsv` | 削除請求受付・対応記録 | 5年 |
| `data/suspension_request_log.tsv` | 利用停止請求受付・対応記録 | 5年 |
| `data/third_party_provision_log.tsv` | 第三者提供記録台帳 | 3年 |

### 6.2 台帳共通フォーマット

```
受付日	請求種別	請求者メール	firebase_uid	対応完了日	対応者	備考
```

---

## 7. SLA まとめ

| 請求種別 | SLA（法定） | 本サービス目標 |
| :--- | :--- | :--- |
| 開示 | 速やかに（法定なし・実務慣行2週間） | **2週間以内** |
| 訂正 | 速やかに | **2週間以内** |
| 削除 | 速やかに（GDPR: 30日以内） | **2週間以内** |
| 利用停止 | 速やかに | **3営業日以内** |

---

## 8. 関連ドキュメント

- [ユーザーデータ完全消去フロー設計書](USER_DATA_DELETION_FLOW.md)
- [個人情報同意書テンプレート](PILOT_CONSENT_TEMPLATE.md)
- [システム監査ログ 氏名マスキング・暗号化パイプライン設計書](AUDIT_LOG_MASKING_AND_ENCRYPTION.md)
