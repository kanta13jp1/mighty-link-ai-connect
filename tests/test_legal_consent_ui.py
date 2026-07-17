from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGAL_DOC_LINKS = [
    "docs/TERMS_OF_SERVICE.md",
    "docs/PRIVACY_POLICY.md",
    "docs/TOKUSHOHO_NOTATION.md",
    "docs/BILLING_AND_REFUND_POLICY.md",
]


def assert_legal_consent_ui(html: str):
    assert 'id="legal-consent-checkbox"' in html
    assert 'id="legal-consent-status"' in html
    assert 'const legalConsentVersion = "MSB-LEGAL-2026-06-DRAFT";' in html
    assert "legal_consent_accepted" in html
    assert "legal_consent_version" in html
    assert "getLegalConsentPayload()" in html
    assert "診断を実行するには、利用規約・プライバシーポリシー等への同意が必要です。" in html
    assert "<h3>法定・規約</h3>" in html
    for link in LEGAL_DOC_LINKS:
        assert html.count(link) >= 2


def assert_legal_consent_discoverability(html: str):
    """T895: 同意欄が画面上部にありデモから遠いため、同意エラー時に
    場所を示す導線（スクロール+ハイライト+ジャンプボタン）を固定する。"""
    assert "function focusLegalConsentPanel()" in html
    assert "function updateLegalConsentAffordances()" in html
    # 同意パネルへのスクロールとハイライト。html{scroll-behavior:smooth}は
    # behavior:"auto"にも効くため、reduced-motion時は"instant"を使う
    assert 'panel.scrollIntoView({behavior: reduceMotion ? "instant" : "smooth", block: "center"});' in html
    assert 'panel.classList.add("consent-attention");' in html
    assert ".legal-consent-panel.consent-attention" in html
    assert "@keyframes consent-attention-pulse" in html
    # reduced-motion ではアニメーションを無効化する
    assert html.index("@keyframes consent-attention-pulse") < html.index(
        ".legal-consent-panel.consent-attention {\n                animation: none;"
    )
    # スクリーンリーダー向け: フォーカス移動の理由をaria-describedby先
    # (#legal-consent-status)へ反映してからフォーカスを移す
    focus_fn_start = html.index("function focusLegalConsentPanel()")
    focus_fn_end = html.index("function updateLegalConsentAffordances()")
    focus_fn = html[focus_fn_start:focus_fn_end]
    assert "setLegalConsentStatus(\"診断を実行するには、利用規約・プライバシーポリシー等への同意が必要です。\", \"var(--rose)\");" in focus_fn
    assert focus_fn.index("checkbox.focus({preventScroll: true});") < focus_fn.index("panel.scrollIntoView")
    # デモのステータスはSRへ通知されるlive regionにする
    assert 'id="aptitude-demo-status" role="status"' in html
    # 自己診断デモ内の常設ジャンプボタン（同意済みで非表示）
    assert 'id="aptitude-demo-consent-jump"' in html
    assert 'onclick="focusLegalConsentPanel()"' in html
    assert 'jump.style.display = accepted ? "none" : "";' in html
    # 質問生成・評価・サーバー側拒否の3経路すべてが同意欄へ誘導する
    assert html.count("focusLegalConsentPanel();") >= 3
    # 同意版数不一致(古いHTMLキャッシュ)はチェック操作で解消できないため、
    # ハイライト誘導ではなく再読み込み案内を出す
    assert '"Invalid legal consent version"' in html
    assert "ページを再読み込みしてから、もう一度同意して実行してください。" in html
    assert html.index('reason.indexOf("Invalid legal consent version")') < html.index(
        'reason.indexOf("legal consent")'
    )
    # チェック変更へ表示を追従させる配線
    assert 'legalConsentCheckbox.addEventListener("change", updateLegalConsentAffordances);' in html


def test_public_index_has_legal_consent_discoverability():
    html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    assert_legal_consent_discoverability(html)


def test_src_index_has_legal_consent_discoverability():
    html = (PROJECT_ROOT / "src" / "index.html").read_text(encoding="utf-8")
    assert_legal_consent_discoverability(html)


def test_public_index_has_legal_consent_ui_and_footer_links():
    html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    assert_legal_consent_ui(html)


def test_src_index_has_legal_consent_ui_and_footer_links():
    html = (PROJECT_ROOT / "src" / "index.html").read_text(encoding="utf-8")
    assert_legal_consent_ui(html)
