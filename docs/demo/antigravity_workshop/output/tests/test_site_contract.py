import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PRODUCTS = {
    "codex": "Codex",
    "claude-code": "Claude Code",
    "claude-cowork": "Claude Cowork",
    "kiro": "Kiro",
    "antigravity": "Antigravity",
}
EXPECTED_VERSIONS = {
    "codex": "0.147.0",
    "claude-code": "2.1.229",
    "claude-cowork": "公開版番号なし（SaaS）",
    "kiro": "1.0.293",
    "antigravity": "2.8.0",
}
COMPARISON_FIELDS = {
    "主な仕事",
    "操作面",
    "進め方",
    "持続指示",
    "能力拡張",
    "MCP・連携",
    "ブラウザ",
    "並列・バックグラウンド",
    "自動化・組み込み",
    "証拠とレビュー",
    "安全境界",
    "価格・利用枠",
    "導入時の注意",
}
ALLOWED_HOSTS = {
    "developers.openai.com",
    "learn.chatgpt.com",
    "chatgpt.com",
    "github.com",
    "code.claude.com",
    "claude.com",
    "support.claude.com",
    "cdn.prod.website-files.com",
    "kiro.dev",
    "antigravity.google",
    "www.youtube.com",
}


def load_products():
    raw = (ROOT / "product-data.js").read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"window\.PRODUCT_DATA\s*=\s*(\[.*\]);", raw, re.DOTALL)
    if not match:
        raise AssertionError("product-data.js must be a JSON array assigned to window.PRODUCT_DATA")
    return json.loads(match.group(1))


class SiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = load_products()
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "styles.css").read_text(encoding="utf-8")

    def test_exact_product_scope(self):
        actual = {item["id"]: item["name"] for item in self.products}
        self.assertEqual(actual, EXPECTED_PRODUCTS)

    def test_removed_rehearsal_products_are_absent(self):
        current = self.html + self.app + json.dumps(self.products, ensure_ascii=False)
        for stale_name in ("Devin", "Cursor Agent", "Windsurf", "Copilot Workspace"):
            self.assertNotIn(stale_name, current)

    def test_icons_are_local_nonempty_and_official(self):
        for product in self.products:
            with self.subTest(product=product["name"]):
                self.assertFalse(urlparse(product["icon"]).scheme)
                icon_path = ROOT / product["icon"]
                self.assertTrue(icon_path.is_file())
                self.assertGreater(icon_path.stat().st_size, 1000)
                self.assert_allowed_url(product["iconSource"])
        self.assertIn("公式アイコン", self.app)

    def test_versions_and_release_dates_are_explicit(self):
        for product in self.products:
            with self.subTest(product=product["name"]):
                release = product["release"]
                self.assertEqual(release["version"], EXPECTED_VERSIONS[product["id"]])
                self.assertRegex(release["date"], r"^2026-\d{2}-\d{2}$")
                self.assert_allowed_url(release["url"])

    def test_latest_update_video_and_blog_are_complete(self):
        for product in self.products:
            for field in ("latestUpdate", "latestVideo", "latestBlog"):
                with self.subTest(product=product["name"], field=field):
                    item = product[field]
                    self.assertTrue(item["title"].strip())
                    self.assertRegex(item["date"], r"^2026-\d{2}-\d{2}$")
                    self.assert_allowed_url(item["url"])

    def test_all_thirteen_comparison_dimensions_exist(self):
        for product in self.products:
            with self.subTest(product=product["name"]):
                self.assertEqual(set(product["comparison"]), COMPARISON_FIELDS)
                self.assertTrue(all(value.strip() for value in product["comparison"].values()))

    def test_source_ledger_has_enough_official_evidence(self):
        source_count = 0
        for product in self.products:
            urls = [source["url"] for source in product["sources"]]
            urls += [
                product["latestUpdate"]["url"],
                product["latestVideo"]["url"],
                product["latestBlog"]["url"],
                product["iconSource"],
            ]
            source_count += len(urls)
            for url in urls:
                self.assert_allowed_url(url)
        self.assertGreaterEqual(source_count, 40)
        self.assertIn('id="source-ledger"', self.html)

    def test_variable_limits_are_not_fabricated(self):
        current = self.html + json.dumps(self.products, ensure_ascii=False)
        for forbidden in ("1日100回", "1日1,000回", "1日1万回", "月3,000 PU", "5hあたり45"):
            self.assertNotIn(forbidden, current)

    def test_accessibility_contract_is_present(self):
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('aria-pressed="true"', self.html)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn("selectedIds.size >= 2", self.app)

    def test_verification_date_and_scripts_are_visible(self):
        self.assertGreaterEqual(self.html.count("2026-08-13"), 2)
        self.assertIn('<script src="product-data.js"></script>', self.html)
        self.assertIn('<script src="app.js"></script>', self.html)

    def test_ten_review_passes_are_recorded(self):
        review_path = ROOT / "SELF_REVIEW.md"
        self.assertTrue(review_path.is_file())
        review = review_path.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^## Review \d{2}:", review, re.MULTILINE)), 10)

    def assert_allowed_url(self, url):
        parsed = urlparse(url)
        self.assertEqual(parsed.scheme, "https")
        self.assertIn(parsed.hostname, ALLOWED_HOSTS)


if __name__ == "__main__":
    unittest.main()
