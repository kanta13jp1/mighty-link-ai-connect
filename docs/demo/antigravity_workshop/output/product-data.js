window.PRODUCT_DATA = [
  {
    "id": "codex",
    "name": "Codex",
    "vendor": "OpenAI",
    "icon": "assets/product-icons/codex.png",
    "iconSource": "https://learn.chatgpt.com/favicon.png",
    "tags": ["development", "automation", "review"],
    "oneLine": "大きなコードベースを読み、実装・テスト・レビュー・公開まで進めるソフトウェア開発エージェント。",
    "bestFor": "複数リポジトリや長い開発タスクを、ローカル・クラウド・モバイルから継続したいチーム",
    "notIdealFor": "非技術部門の定型事務だけを、コードやGitを意識せず処理したい場合",
    "release": {
      "version": "0.147.0",
      "date": "2026-08-07",
      "label": "Codex CLI",
      "url": "https://github.com/openai/codex/releases/tag/rust-v0.147.0"
    },
    "latestUpdate": {
      "title": "Agent Plugins、会話セクション、MCP 2026-07-28対応",
      "date": "2026-08-07",
      "summary": "持ち運べるAgent Plugins、長い会話の整理、承認の自動レビュー、MCP更新、秘密情報のマスキング強化が追加されました。",
      "url": "https://github.com/openai/codex/releases/tag/rust-v0.147.0"
    },
    "latestVideo": {
      "title": "Codex for Solutions Engineers: Making AI Tangible for Customers",
      "date": "2026-07-01",
      "channel": "OpenAI公式 Codex Videos",
      "url": "https://www.youtube.com/watch?v=08hgAtg-P_8"
    },
    "latestBlog": {
      "title": "Custom Code Review rules for Codex",
      "date": "2026-07-20",
      "url": "https://learn.chatgpt.com/blog/custom-code-review-rules-for-codex"
    },
    "comparison": {
      "主な仕事": "コード理解、実装、修正、テスト、PRレビュー、移行、公開",
      "操作面": "Codex app、CLI、IDE拡張、クラウド、GitHub、SDK",
      "進め方": "コードベースを探索し、計画・編集・コマンド・検証を一つのタスクとして継続",
      "持続指示": "AGENTS.md、Rules、設定プロファイル",
      "能力拡張": "Skills、Agent Plugins、Hooks、subagents",
      "MCP・連携": "MCP、GitHub、Slack、Linear、Codex Apps",
      "ブラウザ": "Codex appのBrowser / Computer Use。Web検証や公開確認まで一続きにできる",
      "並列・バックグラウンド": "subagents、クラウド環境、worktree、長時間タスク",
      "自動化・組み込み": "Codex SDK、App Server、GitHub Action、非対話実行、MCP Server",
      "証拠とレビュー": "差分、コマンド出力、テスト、PRレビュー、Appshots、承認履歴",
      "安全境界": "sandbox、approval policy、permission profiles、network policy、Auto-review",
      "価格・利用枠": "Freeは限定利用。Plus/Pro/Business/Enterpriseで拡張。固定回数ではなく作業量とプランで変動",
      "導入時の注意": "広い権限を渡す前にAGENTS.md、sandbox、ネットワーク、承認条件を決める"
    },
    "sources": [
      {"label": "公式ドキュメント", "url": "https://developers.openai.com/codex"},
      {"label": "公式更新履歴", "url": "https://learn.chatgpt.com/docs/changelog"},
      {"label": "公式料金", "url": "https://chatgpt.com/pricing/"},
      {"label": "公式動画一覧", "url": "https://learn.chatgpt.com/videos"}
    ]
  },
  {
    "id": "claude-code",
    "name": "Claude Code",
    "vendor": "Anthropic",
    "icon": "assets/product-icons/claude-code.png",
    "iconSource": "https://code.claude.com/docs/_mintlify/favicons/claude-code/pLsy-mRpNksna2sx/_generated/favicon/android-chrome-192x192.png",
    "tags": ["development", "automation", "review"],
    "oneLine": "ターミナルを中心に、コード編集・Git・サブエージェント・反復ワークフローを深く扱う開発エージェント。",
    "bestFor": "CLIを中心に複数ファイルの変更、Git操作、長い実装、チーム固有の自動化を行う開発者",
    "notIdealFor": "ローカルファイルやターミナルを扱わない一般的な資料作成だけが目的の場合",
    "release": {
      "version": "2.1.229",
      "date": "2026-08-12",
      "label": "Claude Code",
      "url": "https://github.com/anthropics/claude-code/releases/tag/v2.1.229"
    },
    "latestUpdate": {
      "title": "Remote Control継続、Plugin command source、ストリーミング安定化",
      "date": "2026-08-12",
      "summary": "Remote Controlの再開、動的Plugin取得、SSE keepalive、Windows/狭い端末/長文表示のクラッシュ修正、VS Codeのsession groupsが追加されました。",
      "url": "https://github.com/anthropics/claude-code/releases/tag/v2.1.229"
    },
    "latestVideo": {
      "title": "How auto mode works with Claude Code",
      "date": "2026-08-04",
      "channel": "Claude公式チャンネル",
      "url": "https://www.youtube.com/watch?v=b8SV4U6fEIc"
    },
    "latestBlog": {
      "title": "Auto mode is now the default in Claude Code for Pro, Max, and Team plans",
      "date": "2026-08-07",
      "url": "https://claude.com/blog/auto-mode-default-in-claude-code"
    },
    "comparison": {
      "主な仕事": "複数ファイル開発、デバッグ、Git、コードレビュー、移行、反復作業",
      "操作面": "CLI、VS Code、JetBrains、Desktop、Web、Slack",
      "進め方": "ターミナルとコードを往復し、plan・tool call・編集・テストを会話内で反復",
      "持続指示": "CLAUDE.md、auto memory、settings",
      "能力拡張": "Skills、Plugins、Hooks、subagents、Workflows",
      "MCP・連携": "MCP、GitHub、Slack、各種plugin marketplace",
      "ブラウザ": "開発の主軸は端末。必要に応じてMCP、Playwright、Claude in Chromeなどを明示連携",
      "並列・バックグラウンド": "subagents、workflows、Remote Control、cloud sessions",
      "自動化・組み込み": "Claude Agent SDK、headless実行、GitHub Actions、Hooks",
      "証拠とレビュー": "差分、テスト、Git履歴、tool結果、Code Review、workflow結果",
      "安全境界": "permission modes、sandbox、managed settings、MCP allow/deny、hook policy",
      "価格・利用枠": "Pro/Max/Team/EnterpriseまたはAPI。上限はモデル、作業量、プランで変動",
      "導入時の注意": "CLAUDE.mdを短く保ち、HooksとMCPの実行権限をレビューする"
    },
    "sources": [
      {"label": "公式ドキュメント", "url": "https://code.claude.com/docs/en/overview"},
      {"label": "公式リリース", "url": "https://github.com/anthropics/claude-code/releases"},
      {"label": "公式料金", "url": "https://claude.com/pricing"},
      {"label": "公式ブログ", "url": "https://claude.com/blog-category/claude-code"}
    ]
  },
  {
    "id": "claude-cowork",
    "name": "Claude Cowork",
    "vendor": "Anthropic",
    "icon": "assets/product-icons/claude-cowork.png",
    "iconSource": "https://cdn.prod.website-files.com/6889473510b50328dbb70ae6/68c33859cc6cd903686c66a2_apple-touch-icon.png",
    "tags": ["knowledge", "automation"],
    "oneLine": "ファイル、メール、カレンダー、Web、業務ツールをまたぐナレッジワークを委任するエージェント。",
    "bestFor": "調査、表計算、資料作成、週次レポート、営業・経理・法務など複数ツールをまたぐ仕事",
    "notIdealFor": "Git差分やビルド、コードレビューを中心にした本格的なソフトウェア開発",
    "release": {
      "version": "公開版番号なし（SaaS）",
      "date": "2026-07-07",
      "label": "公式Release Notesの最新Cowork項目",
      "url": "https://support.claude.com/en/articles/12138966-release-notes"
    },
    "latestUpdate": {
      "title": "Claude Cowork is now your Chrome side panel",
      "date": "2026-08-12",
      "summary": "公式動画でChromeサイドパネルからCoworkを使う最新の操作面が案内されました。製品はSaaSのため独立したsemantic versionを公開していません。",
      "url": "https://www.youtube.com/watch?v=C-5wF6tkQ2Q"
    },
    "latestVideo": {
      "title": "Claude Cowork is now your Chrome side panel",
      "date": "2026-08-12",
      "channel": "Claude公式チャンネル",
      "url": "https://www.youtube.com/watch?v=C-5wF6tkQ2Q"
    },
    "latestBlog": {
      "title": "Working with Claude Fable 5 in Claude Cowork",
      "date": "2026-07-16",
      "url": "https://claude.com/blog/working-with-claude-fable-5-in-claude-cowork"
    },
    "comparison": {
      "主な仕事": "調査、文書、表計算、プレゼン、ファイル整理、定期レポート、業務オペレーション",
      "操作面": "Desktop、Web、Mobile、Chrome side panel",
      "進め方": "完了条件と参照先を渡し、接続した業務ツールを横断して成果物まで委任",
      "持続指示": "Projects、organization instructions、memory",
      "能力拡張": "Skills、Plugins、Connectors、live artifacts",
      "MCP・連携": "Connectors、remote MCP、Google Workspace、Microsoft 365など",
      "ブラウザ": "Desktopのbrowser/computer useとChrome side panel。Web・Mobileではremote session",
      "並列・バックグラウンド": "remote sessions、scheduled tasks、端末を閉じても続く処理",
      "自動化・組み込み": "定期タスクとConnectorsが中心。開発者向けSDKより業務委任を優先",
      "証拠とレビュー": "生成ファイル、live artifacts、接続先の下書き、人の承認待ち",
      "安全境界": "接続先ごとの権限、送信前レビュー、組織管理、監査・保持設定",
      "価格・利用枠": "Pro/Max/Team/Enterpriseで提供。機能展開と利用上限はプラン・地域・作業量で変動",
      "導入時の注意": "メール送信や更新権限は最小化し、まず下書きと読み取りから始める"
    },
    "sources": [
      {"label": "公式製品ページ", "url": "https://claude.com/product/cowork"},
      {"label": "公式Release Notes", "url": "https://support.claude.com/en/articles/12138966-release-notes"},
      {"label": "公式料金", "url": "https://claude.com/pricing"},
      {"label": "公式利用ガイド", "url": "https://support.claude.com/en/collections/16163169-claude-cowork"}
    ]
  },
  {
    "id": "kiro",
    "name": "Kiro",
    "vendor": "AWS",
    "icon": "assets/product-icons/kiro.svg",
    "iconSource": "https://kiro.dev/icon.svg?fe599162bb293ea0",
    "tags": ["development", "planning", "automation"],
    "oneLine": "Requirements、Design、Tasksを明文化し、仕様駆動で実装へ進む開発エージェント。",
    "bestFor": "要件の曖昧さを減らし、仕様・設計・タスク・実装をレビュー可能な順序で進めたい開発",
    "notIdealFor": "仕様化を省いて、その場の小さな修正だけを最短で終えたい場合",
    "release": {
      "version": "1.0.293",
      "date": "2026-08-11",
      "label": "Kiro IDE",
      "url": "https://kiro.dev/changelog/ide/1-0-293/"
    },
    "latestUpdate": {
      "title": "Cloud Sessions and Agent Focus Mode Upgrades",
      "date": "2026-08-11",
      "summary": "Agent Focus ModeにCloud Sessionsプレビュー、折りたためるsession rail、画面内で応答できるattention card、前後ナビゲーションが追加されました。",
      "url": "https://kiro.dev/changelog/ide/1-0-293/"
    },
    "latestVideo": {
      "title": "Introducing Kiro Crew",
      "date": "2026-08-04",
      "channel": "Kiro公式チャンネル",
      "url": "https://www.youtube.com/watch?v=iOIS1OZLkI0"
    },
    "latestBlog": {
      "title": "Claude Opus 5 is now available in Kiro",
      "date": "2026-07-24",
      "url": "https://kiro.dev/blog/opus-5/"
    },
    "comparison": {
      "主な仕事": "仕様駆動開発、要件分析、設計、タスク分解、実装、バグ修正",
      "操作面": "IDE、CLI、Web、Mobile、Crew",
      "進め方": "Requirements -> Design -> Tasks -> Implementationを承認点付きで進める",
      "持続指示": "Steering、custom agents、workspace settings",
      "能力拡張": "Agent Skills、Powers、Hooks、custom agents",
      "MCP・連携": "MCP、Powersに含めるMCP/知識/Workflow、enterprise registry",
      "ブラウザ": "主軸はIDE内の仕様とコード。Web操作はMCPや外部ツールで目的に応じて追加",
      "並列・バックグラウンド": "Agent Focus、Cloud Sessions、Crew、parallel task execution",
      "自動化・組み込み": "CLI headless、Hooks、automations、spec task execution",
      "証拠とレビュー": "requirements.md、design.md、tasks.md、hunk review、session export",
      "安全境界": "capability-based permissions、workspace trust、supervised review、MCP governance",
      "価格・利用枠": "Free 50 credits。Pro $20/1000、Pro+ $40/2000、Pro Max $100/5000、Power $200/10000（月額）",
      "導入時の注意": "SteeringとPowerはKiro固有名。仕様承認を飛ばす条件をチームで決める"
    },
    "sources": [
      {"label": "公式ドキュメント", "url": "https://kiro.dev/docs/"},
      {"label": "公式Changelog", "url": "https://kiro.dev/changelog/ide/"},
      {"label": "公式料金", "url": "https://kiro.dev/pricing/"},
      {"label": "公式ブログ", "url": "https://kiro.dev/blog/"}
    ]
  },
  {
    "id": "antigravity",
    "name": "Antigravity",
    "vendor": "Google",
    "icon": "assets/product-icons/antigravity.png",
    "iconSource": "https://antigravity.google/assets/image/antigravity-logo.png",
    "tags": ["development", "planning", "automation", "browser"],
    "oneLine": "IDE、Browser、Artifactを一画面でつなぎ、計画から画面検証まで見せながら進める開発エージェント。",
    "bestFor": "WebサイトやUIを、実装・ブラウザ操作・スクリーンショット証拠まで短時間で見せたい場面",
    "notIdealFor": "画面確認が不要で、既存CIだけを最小コストで回す純粋なバックエンド自動化",
    "release": {
      "version": "2.8.0",
      "date": "2026-08-12",
      "label": "Antigravity",
      "url": "https://antigravity.google/changelog?app=antigravity"
    },
    "latestUpdate": {
      "title": "Persistent Sidebar Folders, Crash Fixes, and UI Enhancements",
      "date": "2026-08-12",
      "summary": "sidebar folder状態の保持、大きなcommand outputを含む会話のクラッシュ対策、file/artifact previewとLinux UIの信頼性が改善されました。",
      "url": "https://antigravity.google/changelog?app=antigravity"
    },
    "latestVideo": {
      "title": "Mission Report Ep. 06 | Antigravity Updates",
      "date": "2026-08-11",
      "channel": "Google Antigravity公式チャンネル",
      "url": "https://www.youtube.com/watch?v=tiFLdJJGpno"
    },
    "latestBlog": {
      "title": "Introducing Custom Agents",
      "date": "2026-08-12",
      "url": "https://antigravity.google/blog/introducing-custom-agents"
    },
    "comparison": {
      "主な仕事": "Web開発、UI改善、ブラウザ検証、マルチモーダル制作、デモ、長時間タスク",
      "操作面": "Antigravity 2.0 IDE、CLI、SDK",
      "進め方": "Planning、実装、Browser操作、Artifact確認を同じworkspaceで反復",
      "持続指示": "Rules、Workflows、workspace settings",
      "能力拡張": "Skills、Custom Agents、Hooks、subagents",
      "MCP・連携": "MCP、組み込みBrowser、IDE tools、SDK tools",
      "ブラウザ": "中心機能。Browser操作、Visual Feedback、Screenshot/Recording Artifactで確認",
      "並列・バックグラウンド": "subagents、Custom Agents、Scheduled Tasks、Agent Manager",
      "自動化・組み込み": "Antigravity CLI、Antigravity SDK、read-onlyを含むtool policy",
      "証拠とレビュー": "Plan、diff、Browser、Screenshot、Recording、Walkthrough、Artifact",
      "安全境界": "permissions、tool approval、MCP設定、workspace単位のRules、read-only tool構成",
      "価格・利用枠": "Google AI Pro $20、Ultra $100（5x）/ $200（20x）の案内。quotaは共有capacity型で固定回数ではない",
      "導入時の注意": "Artifactが成功していても、本番公開・外部書き込みは人が明示承認する"
    },
    "sources": [
      {"label": "公式ドキュメント", "url": "https://antigravity.google/docs/features?app=antigravity"},
      {"label": "公式Changelog", "url": "https://antigravity.google/changelog?app=antigravity"},
      {"label": "公式料金更新", "url": "https://antigravity.google/blog/changes-to-antigravity-plans"},
      {"label": "公式ブログ", "url": "https://antigravity.google/blog"}
    ]
  }
];
