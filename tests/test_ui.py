import os
import sys
import time
import subprocess
import httpx
import pytest
from playwright.sync_api import sync_playwright

# Ensure src directory is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

@pytest.fixture(scope="module")
def fastapi_server():
    # Start uvicorn server in a subprocess on port 8085
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8085"],
        cwd=os.path.join(PROJECT_ROOT, "src"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the server to start by polling /api/health
    for _ in range(30):
        try:
            r = httpx.get("http://127.0.0.1:8085/api/health")
            if r.status_code == 200:
                break
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    else:
        server_process.terminate()
        stdout, stderr = server_process.communicate()
        raise RuntimeError(f"Server failed to start on port 8085. Stdout: {stdout}, Stderr: {stderr}")
        
    yield "http://127.0.0.1:8085"
    
    server_process.terminate()
    server_process.wait()

def test_ui_flow(fastapi_server):
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to homepage
        page.goto(fastapi_server)
        
        # 1. Verify Page Title
        assert "Mighty Skill-Bridge" in page.title()
        
        # 2. Verify "MightyLINK HP" navigation link is present and correct
        hp_link = page.locator("a:has-text('MightyLINK HP')")
        assert hp_link.count() > 0
        assert hp_link.first.get_attribute("href") == "exports/mighty-link-hp/index.html"
        
        # 3. Check text areas are initially empty
        eng_input = page.locator("#engineer-input")
        job_input = page.locator("#job-input")
        assert eng_input.input_value() == ""
        assert job_input.input_value() == ""
        
        # 4. Click the first "Load Sample" button (for engineer resume)
        # Note: We click the first element matching the sample-btn class
        page.locator(".sample-btn", has_text="Load Sample").nth(0).click()
        assert len(eng_input.input_value()) > 0
        
        # 5. Click the second "Load Sample" button (for job details)
        page.locator(".sample-btn", has_text="Load Sample").nth(1).click()
        assert len(job_input.input_value()) > 0
        
        # 6. Click the "Analyze Fit" button
        analyze_btn = page.locator("button.big-btn")
        analyze_btn.click()
        
        # 7. Verify that the report section is active and displays a non-zero score
        page.wait_for_selector("#report-section.active", timeout=5000)
        page.wait_for_function("document.getElementById('gauge-score').textContent !== '0'")
        
        score_val = page.locator("#gauge-score").text_content()
        assert int(score_val) > 0
        print(f"[+] UI flow verified. Matching score: {score_val}%")
        
        # 8. Verify that skills badges are populated in the DOM
        matched_badges = page.locator("#matched-skills-container .matched-badge")
        missing_badges = page.locator("#missing-skills-container .missing-badge")
        page.wait_for_function("document.querySelectorAll('#matched-skills-container .matched-badge').length > 0")
        
        assert matched_badges.count() > 0
        assert missing_badges.count() > 0
        print(f"[+] Verified matched ({matched_badges.count()}) and missing ({missing_badges.count()}) skills badges are rendered successfully.")

        # 9. Verify support form can submit through the FastAPI endpoint
        page.locator("#support").scroll_into_view_if_needed()
        page.locator("#support-category").select_option("technical")
        page.locator("#support-email").fill("ui-support@example.test")
        page.locator("#support-subject").fill("UI smoke support request")
        page.locator("#support-message").fill("The support contact form is visible and accepts a smoke-test request.")
        page.locator("#support-submit").click()
        page.wait_for_function("document.getElementById('support-status').textContent === '送信済み'")
        assert page.locator("#support-status").text_content() == "送信済み"
        
        browser.close()
