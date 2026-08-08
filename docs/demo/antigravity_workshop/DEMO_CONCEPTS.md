# Antigravityデモで扱う4概念

## Steering

人がImplementation Plan、コード差分、ブラウザ結果などのArtifactへフィードバックし、次の実行方向を修正する操作。今回のデモでは、初版サイトへ「変更すること／維持すること／検証すること」を明示して機能とデザインを改善する。

## Skills

特定作業の手順、ベストプラクティス、任意のスクリプトや資料をまとめた再利用可能なパッケージ。基本単位は`SKILL.md`で、会話開始時は名前と説明だけを発見し、必要時に全文を読み、実行時に手順へ従う。

今回使うSkill:

- `/grill-me`: 実装前に質問を重ね、要件・除外・停止条件・成功条件を明確にする。
- `/find-skills`: skills.shとSkills CLIを使い、用途に合うSkillを検索し、公開元・利用実績・監査情報を確認する。

2026年8月8日の`npx skills find "frontend design"`では、`anthropics/skills@frontend-design`が第一候補。skills.sh表示で約75.5万インストール、GitHub約16.7万stars、3つのセキュリティ監査がPassだった。デモでは検索と品質確認まで行い、インストールはしない。

## MCP

Model Context Protocol。AIエージェントとローカルツール、データベース、外部APIを標準形式で接続し、構造化されたContextの読取りや許可されたTool実行を可能にする。今回のデモではGitHub MCPを読み取り専用で使い、公開先のbranch、commit、deploymentを確認する。未接続なら会場で認証を始めず省略する。

## Power

この資料では、公式機能名ではなく「Steering、Skills、MCP、Browser、権限管理を組み合わせ、AIの提案を検証可能な成果へ変える実行力」を表す研修上の呼称として使う。製品UIに`Power`という独立設定があるとは説明しない。

## 公式参照

- [ArtifactsとSteering](https://antigravity.google/docs/artifacts)
- [Agent Skills](https://antigravity.google/docs/skills)
- [MCP](https://antigravity.google/docs/mcp)
- [RulesとWorkflows](https://antigravity.google/docs/rules-workflows)
- [Permissions](https://antigravity.google/docs/permissions?app=antigravity)
- [Skills directory](https://skills.sh/)
