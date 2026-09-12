import os
import sys
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME

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
    
    # Listen to console logs and errors
    page.on("console", lambda msg: print(f"[BROWSER CONSOLE {msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: print(f"[BROWSER ERROR] {exc}"))
    
    page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded")
    
    print("Page Title:", page.title())
    
    nav = page.locator("#primary-navigation a[href='#survey-section']")
    print("Nav Count:", nav.count())
    if nav.count() > 0:
        print("Nav Initial Text:", nav.text_content())
    
    en_btn = page.locator(".language-switch button[data-lang='en']")
    print("EN btn count:", en_btn.count())
    if en_btn.count() > 0:
        en_btn.click(no_wait_after=True)
        print("Clicked EN button!")
    
    page.wait_for_timeout(2000)
    print("Nav Text after EN click:", nav.text_content())
    print("Document lang attr:", page.evaluate("document.documentElement.lang"))
    
    browser.close()
