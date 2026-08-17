import asyncio
from playwright.async_api import async_playwright
import httpx
import subprocess
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME

async def main():
    port = 59124
    env = dict(os.environ)
    env["AI_FORCE_MOCK"] = "true"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=os.path.join(PROJECT_ROOT, "src"),
        env=env
    )
    await asyncio.sleep(2)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            http_credentials={
                "username": BASIC_AUTH_USERNAME,
                "password": BASIC_AUTH_PASSWORD,
            }
        )
        await context.add_init_script("""
            localStorage.setItem('mighty_auth_session', JSON.stringify({ email: 'qa@mightylink-app.com', token: 'mock' }));
        """)
        page = await context.new_page()
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        
        await page.goto(f"http://127.0.0.1:{port}", wait_until="domcontentloaded")
        await asyncio.sleep(1)
        
        # Test 1: Language switch
        print("[*] Testing language switch...")
        en_btn = page.locator(".language-switch a[data-lang='en']")
        print(f"[*] en_btn count: {await en_btn.count()}")
        await en_btn.click(no_wait_after=True)
        await asyncio.sleep(0.5)
        nav_text = await page.locator("#primary-navigation a[href='#survey-section']").text_content()
        print(f"[*] Nav text after EN click: {repr(nav_text)}")
        
        # Test 2: Training link click
        print("[*] Testing training tab click...")
        tr_link = page.locator("#primary-navigation a[href='#training-section']")
        print(f"[*] tr_link count: {await tr_link.count()}")
        await tr_link.click(no_wait_after=True)
        await asyncio.sleep(0.5)
        is_vis = await page.locator("#training-section").is_visible()
        print(f"[*] #training-section is_visible: {is_vis}")
        
        await browser.close()
        
    proc.terminate()
    proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
