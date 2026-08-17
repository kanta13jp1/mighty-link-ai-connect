import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME

server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app:app", "--port", "58777", "--host", "127.0.0.1"],
    cwd=os.path.join(PROJECT_ROOT, "src"),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(3)

try:
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
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: print(f"[ERROR] {exc}"))

        page.goto("http://127.0.0.1:58777", wait_until="domcontentloaded")

        link = page.locator("#primary-navigation a[href='#training-section']")
        print("Training link count:", link.count())

        # Click link
        link.click()
        page.wait_for_timeout(1000)

        sect = page.locator("#training-section")
        print("Training section count:", sect.count())
        print("Training section is_visible:", sect.is_visible())
        print("Training section class:", sect.get_attribute("class"))
        print("Training section computed display:", page.evaluate("window.getComputedStyle(document.getElementById('training-section')).display"))
        print("Active tab in JS:", page.evaluate("typeof currentActiveTabId !== 'undefined' ? currentActiveTabId : 'undefined'"))

        browser.close()
finally:
    server_proc.kill()
