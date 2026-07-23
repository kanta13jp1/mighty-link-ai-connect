import os
import sys
import time
import subprocess
import httpx
import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

@pytest.fixture(scope="module")
def fastapi_server():
    # Start uvicorn server in a subprocess on port 8087
    # Note: We do not redirect stdout/stderr to PIPE, to let logs flow to pytest output or console
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8087"],
        cwd=os.path.join(PROJECT_ROOT, "src")
    )
    
    # Wait for the server to start
    for _ in range(40):
        try:
            r = httpx.get("http://127.0.0.1:8087/api/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        server_process.terminate()
        server_process.wait()
        raise RuntimeError("Server failed to start on port 8087.")
        
    yield "http://127.0.0.1:8087"
    
    server_process.terminate()
    server_process.wait()

def test_language_switch_flow(fastapi_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Open main page
        page.goto(fastapi_server)
        
        # 1. Default should display JP text or fall back to JP
        page.wait_for_selector("#primary-navigation")
        nav_text = page.locator("#primary-navigation a[href='#survey-section']").text_content()
        assert "アンケート" in nav_text or "Survey" in nav_text
        
        # 2. Click "EN" language switch
        en_btn = page.locator(".language-switch a[data-lang='en']")
        en_btn.click()
        
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
        zh_btn.click()
        page.wait_for_function(
            "document.documentElement.lang === 'zh'"
        )
        assert page.evaluate("document.documentElement.lang") == "zh"
        
        # 4. Click "KO" (ko)
        ko_btn = page.locator(".language-switch a[data-lang='ko']")
        ko_btn.click()
        page.wait_for_function(
            "document.documentElement.lang === 'ko'"
        )
        assert page.evaluate("document.documentElement.lang") == "ko"
        
        # 5. Switch back to "EN" and verify localStorage persistence
        page.locator(".language-switch a[data-lang='en']").click()
        page.wait_for_function("document.documentElement.lang === 'en'")
        
        page.reload()
        page.wait_for_selector("#primary-navigation")
        
        assert page.evaluate("document.documentElement.lang") == "en"
        nav_text_after = page.locator("#primary-navigation a[href='#survey-section']").text_content()
        assert "Survey" in nav_text_after
        
        browser.close()
