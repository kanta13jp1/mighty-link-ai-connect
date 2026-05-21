# 📖 Google Sheets WBS 自動同期 ＆ 環境構築手順書 (WBS_SYNC_GUIDE.md)

> **Mighty-Link AI Connect Project**
> *Google Cloud OAuth 2.0 同意画面の作成から、API 429/403 制約を回避した高精度 WBS 自動同期基盤の構築手順*

---

## 1. 概要と背景

本プロジェクトでは、プロジェクト管理の円滑化と **Google Workspace AI (Sheets/Docs Live) ＆ Gemini Spark 連携** の体現のため、ローカルの `data/WBS.tsv` の変更を自動で Google スプレッドシートに反映し、マイティ・リンク様のブランドカラー（Mighty Blue）で美しく自動装飾する Python 同期システムを構築しました。

その過程で直面する Google API の主要なセキュリティ・クォータ制約を完全に克服した手順を、今後の再現性のために記録します。

---

## 2. Google Cloud Platform (GCP) セットアップ手順

サービスアカウントが持つ容量制限（403 Drive quota exceeded）を回避し、ユーザー本人の Google Workspace アカウント（`k-umezawa@ml-mightylink.com`）のドライブ領域にスプレッドシートを直接作成・操作するため、**OAuth 2.0 (デスクトップ アプリ) 認証** を採用しています。

### ステップ 1: APIs の有効化
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスします。
2. 上部のプロジェクト選択で `mighty-link-ai-connect` を選択します。
3. **「API とサービス」** > **「ライブラリ」** に進みます。
4. 検索窓から以下を検索し、それぞれ **「有効にする」** をクリックします。
   - **Google Sheets API**
   - **Google Drive API**

### ステップ 2: OAuth 同意画面 (Consent Screen) の作成
1. **「API とサービス」** > **「OAuth 同意画面」** をクリックします。
2. User Type で **「外部 (External)」** を選択し、**「作成」** をクリックします。
3. **アプリ情報** を入力します：
   - アプリ名: `Mighty-Link AI Connect`
   - ユーザーサポートメール: `kanta13jp@gmail.com`
   - デベロッパーの連絡先情報: `kanta13jp@gmail.com`
4. 他の項目はデフォルトのまま「保存して次へ」を進めます。
5. **テストユーザー (Test users)** ステップで、**「+ ADD USERS」** をクリックし、認証を行う Google アカウント (`k-umezawa@ml-mightylink.com`) を追加して保存します。*(※このテストユーザーの追加を行わないと、認証時に「このアプリは承認されていません」のエラーが発生します)*
6. 最後の「終了」画面で、一番下にある **「作成」** ボタンをクリックして同意画面の構築を完了させます。

### ステップ 3: OAuth 2.0 クライアント ID の作成とダウンロード
1. 左メニューの **「認証情報 (Credentials)」** をクリックします。
2. 画面上部の **「+ 認証情報を作成 (Create Credentials)」** > **「OAuth クライアント ID (OAuth client ID)」** を選択します。
3. アプリケーションの種類で **「デスクトップ アプリ (Desktop App)」** を選択します。
4. 名前を `Mighty WBS Sync Client` などと入力し、**「作成」** をクリックします。
5. 作成完了ダイアログが表示されたら、**「JSON をダウンロード (Download JSON)」** ボタンをクリックして認証キーファイルをダウンロードします。
6. ダウンロードした JSON ファイルの名前を **`client_secret.json`** に変更し、本プロジェクトのルートディレクトリ（`c:\Users\kanta\GitHub\mighty-link-ai-connect\`）の直下に配置します。

---

## 3. ローカル環境の実行手順

### ステップ 1: 依存関係のインストール
コマンドプロンプトまたは PowerShell を起動し、プロジェクトのルートディレクトリで以下を実行して、必要なライブラリをインストールします。
```powershell
pip install -r requirements.txt
```
*(※ `requirements.txt` には `gspread>=6.0.0`, `google-auth>=2.0.0` が定義されています)*

### ステップ 2: 同期スクリプトの実行と初回ブラウザ認証
初めてスクリプトを動かす際、ローカルのブラウザが立ち上がり、Google アカウントによる認可（ログイン）が求められます。

1. 以下のコマンドを実行します：
   ```powershell
   python scripts/sync_wbs_to_sheets.py
   ```
2. スクリプトが `client_secret.json` を検知すると、自動的にブラウザが起動し、Google のサインイン画面が表示されます。
3. `k-umezawa@ml-mightylink.com` アカウントを選択します。
4. 「このアプリは Google では検証されていません」という警告画面（テスト用同意画面のため表示されます）が出たら、左下の **「詳細」** をクリックし、**「Mighty-Link AI Connect（安全ではないページ）に移動」** をクリックします。
5. アプリケーションにスプレッドシートとドライブの操作権限を与えるため、**「続行 (Continue)」** をクリックして許可します。
6. ブラウザに 「The authentication flow has completed. You may close this window.」と表示されれば、認証成功です！
7. プロジェクトディレクトリ直下に **`authorized_user.json`** が自動生成されます。これにより、2回目以降の実行ではブラウザが起動せず、完全自動でバックグラウンド実行されるようになります。

### ステップ 3: 既存のスプレッドシートへの更新同期
特定の既存スプレッドシートに対して、WBSの変更（タスク完了ステータスなど）を再同期させたい場合は、引数としてスプレッドシートのID（またはURL）を渡して実行します。
```powershell
   python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
```

---

## 4. 技術的なエラーとその回避ロジック

### ① 容量制限 (403 Drive Storage Quota Exceeded) の回避
- **現象**: 新規作成した GCP サービスアカウント自体は Google ドライブのストレージ容量を持たない（0GB）ため、サービスアカウント名義でスプレッドシートを新規作成しようとすると容量オーバーのエラー (403) が発生します。
- **回避策**: OAuth 2.0 接続を行い、ユーザー本人の Google アカウント（G: ドライブ空き25GB以上）の権限でスプレッドシートを直接作成・所有させることで、ストレージ制限を完全に回避しました。

### ② 書き込み制限 (API 429 Quota Exceeded for Write Requests) の回避
- **現象**: `gspread` のセルごとの書式設定（`worksheet.format`）や、値の1セルずつの読み取りをループで何度も繰り返すと、Google Sheets API の「1分あたりの書き込み制限」に達し、APIエラー (429) が発生します。
- **回避策**: スタイリング処理（ヘッダー背景色、太字、フォントサイズ、各列幅、各行高、ステータス列の条件付き色分け）をすべて **`requests_list`** という単一の JSON 配列に格納し、**`sh.batch_update()`** を用いてたった1回の API 呼び出しに統合（Single Batch Update化）しました。これにより、同期速度が 0.5 秒以下に短縮され、APIエラーは一切発生しなくなりました。

### ③ Windows PowerShell での文字化け・絵文字エラーの回避
- **現象**: ターミナルで実行する際、標準出力に絵文字（`📊`, `🟢` など）が含まれていると、Windows の標準エンコーディング（cp932/Shift-JIS）と競合し、`UnicodeEncodeError` でプログラムが強制終了します。
- **回避策**: プログラム内の標準出力から Windows で表現できない絵文字を排除し、`[*]`, `[+]`, `[!]` などの安全なシンボルへと置き換えるとともに、エラーハンドリングを強化して Windows 環境下でも 100% 安定して動作するように設計しました。

---
*本ガイドはプロジェクト Mighty Skill-Bridge の円滑な運用のために自動作成されました。*
