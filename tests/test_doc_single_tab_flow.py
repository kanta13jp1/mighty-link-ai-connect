# -*- coding: utf-8 -*-
"""
tests/test_doc_single_tab_flow.py
Verify that document navigation and training handbook links open in the SAME tab
without creating duplicate tabs, and return smoothly to Home.
"""

import os
import sys
import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME


def test_training_and_doc_single_tab_navigation(fastapi_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            http_credentials={
                "username": BASIC_AUTH_USERNAME,
                "password": BASIC_AUTH_PASSWORD,
            }
        )
        context.add_init_script("""
            localStorage.setItem('mighty_auth_session', JSON.stringify({ email: 'qa@mightylink-app.com', token: 'mock' }));
        """)
        page = context.new_page()
        page.set_default_timeout(10_000)
        page.set_default_navigation_timeout(30_000)
        page.route("**/*.mp4", lambda route: route.abort())

        # 1. Open App
        page.goto(fastapi_server, wait_until="domcontentloaded")
        assert len(context.pages) == 1, "Must start with exactly 1 tab"

        # 2. Click Training Guide link in Sidebar
        page.wait_for_selector("#primary-navigation a[href='#training-section']")
        page.locator("#primary-navigation a[href='#training-section']").click(force=True)
        page.wait_for_selector("#training-section", state="visible")
        assert page.locator("#training-section").is_visible(), "Training Section must be visible as an App Tab"

        # 3. Assert NO modal is open
        assert page.locator("#training-modal").count() == 0, "Old training modal must not exist in DOM"

        # 4. Click handbook link
        handbook_link = page.locator("#training-section a[href*='FOUNDATION_TRAINING_HANDBOOK']").first
        handbook_link.click()

        # Wait for doc page to load
        page.wait_for_selector(".doc-container, .markdown-body")
        assert len(context.pages) == 1, "Must remain in exactly 1 tab (no duplicate tabs spawned)"

        # 5. Verify back to home
        back_btn = page.locator(".back-link, a:has-text('ホームに戻る')").first
        back_btn.click()

        page.wait_for_selector("#primary-navigation")
        assert len(context.pages) == 1, "Must still be in exactly 1 tab after returning home"

        browser.close()
