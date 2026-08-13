# ローカル予備成果物

AI Agent Learning Hubの完成版です。`index.html`をブラウザで開くと、Codex、Claude Code、Claude Cowork、Kiro、Antigravityの5製品を用途で絞り込み、最大2製品を比較できます。

`TEST_SPEC.md`は実装前に固定する10ケースの正本、`tests/test_site_contract.py`はT01-T08を依存追加なしで確認する契約テストです。

この成果物はデモ中に90秒以上進展がない場合の切替先です。外部ライブラリ、外部画像、外部フォント、フォーム送信、ネットワーク送信、永続保存を使用しません。

確認条件:

- すべて: 5件
- 開発: 4件
- ナレッジワーク: 1件
- 計画・自動化: 5件
- 比較: 最大2製品。3製品目は追加せず案内を表示
- viewport: 1440x900、390x844

```powershell
python -m unittest discover -s tests -v
```
