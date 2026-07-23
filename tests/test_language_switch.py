import os
import sys
import time
import subprocess
import httpx
import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME


def test_language_switch_flow(fastapi_server):
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
        
        # Open main page
        page.goto(fastapi_server, wait_until="domcontentloaded")
        
        # 1. Default should display JP text or fall back to JP
        page.wait_for_selector("#primary-navigation", state="attached")
        nav_text = page.locator("#primary-navigation a[href='#survey-section']").text_content()
        assert "アンケート" in nav_text or "Survey" in nav_text
        
        # 2. Click "EN" language switch
        en_btn = page.locator(".language-switch a[data-lang='en']")
        en_btn.click(no_wait_after=True)
        
        # Verify DOM update
        page.wait_for_function(
            "document.querySelector('#primary-navigation a[href=\"#survey-section\"]').textContent.includes('Survey')"
        )
        lang_attr = page.evaluate("document.documentElement.lang")
        assert lang_attr == "en"
        
        # Check placeholder update
        res_placeholder = page.locator("#engineer-input").get_attribute("placeholder")
        assert "profile" in res_placeholder.lower() or "skills" in res_placeholder.lower()
        
        # 3. Click "中文" (zh)
        zh_btn = page.locator(".language-switch a[data-lang='zh']")
        zh_btn.click(no_wait_after=True)
        page.wait_for_function(
            "document.documentElement.lang === 'zh'"
        )
        assert page.evaluate("document.documentElement.lang") == "zh"
        
        # 4. Click "KO" (ko)
        ko_btn = page.locator(".language-switch a[data-lang='ko']")
        ko_btn.click(no_wait_after=True)
        page.wait_for_function(
            "document.documentElement.lang === 'ko'"
        )
        assert page.evaluate("document.documentElement.lang") == "ko"
        
        # 5. Switch back to "EN" and verify localStorage persistence
        page.locator(".language-switch a[data-lang='en']").click(no_wait_after=True)
        page.wait_for_function("document.documentElement.lang === 'en'")
        
        page.reload(wait_until="domcontentloaded")
        page.evaluate("if (typeof closeAuthModal === 'function') closeAuthModal(true);")
        page.wait_for_selector("#primary-navigation")
        
        assert page.evaluate("document.documentElement.lang") == "en"
        nav_text_after = page.locator("#primary-navigation a[href='#survey-section']").text_content()
        assert "Survey" in nav_text_after
        
        browser.close()
