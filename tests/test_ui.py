import os
import sys
import time
import subprocess
import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME


def test_ui_flow(fastapi_server):
    with sync_playwright() as p:
        # Launch headless browser
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
        
        # Navigate to homepage
        page.goto(fastapi_server, wait_until="domcontentloaded")
        
        # 1. Verify Page Title
        assert "Mighty Skill-Bridge" in page.title()
        
        # 2. Verify the internal employee-system navigation links are present
        expected_links = {
            "#survey-section",
            "#attendance-section",
            "#matching-section",
            "#admin-dashboard-section",
        }
        actual_links = {
            href for href in page.locator("#primary-navigation a").evaluate_all(
                "(links) => links.map((link) => link.getAttribute('href'))"
            )
        }
        assert expected_links.issubset(actual_links)
        assert page.locator("#admin-dashboard-username").count() == 1
        assert page.locator("#admin-dashboard-password").count() == 1
        assert page.locator("#support").count() == 1
        
        
        # 3. Check text areas are initially empty
        eng_input = page.locator("#engineer-input")
        job_input = page.locator("#job-input")
        assert eng_input.input_value() == ""
        assert job_input.input_value() == ""
        
        # 4. Click the first sample load button (for engineer resume)
        page.wait_for_selector(".hero-inputs-container .sample-btn")
        page.locator(".hero-inputs-container .sample-btn").nth(0).click(force=True)
        expect(eng_input).not_to_have_value("")
        assert len(eng_input.input_value()) > 0
        
        # 5. Click the second sample load button (for job details)
        page.locator(".hero-inputs-container .sample-btn").nth(1).click(force=True)
        expect(job_input).not_to_have_value("")
        assert len(job_input.input_value()) > 0
        
        # 6. Verify Analyze requires legal consent, then accept and run
        analyze_btn = page.locator("#run-analysis-btn")
        analyze_btn.click()
        expect(page.locator("#legal-consent-status")).to_contain_text("同意が必要")
        page.locator("#legal-consent-checkbox").check()
        analyze_btn.click()
        
        # 7. Verify that the report section is active and displays a non-zero score
        page.wait_for_selector("#report-section.active", timeout=5000)
        expect(page.locator("#gauge-score")).not_to_have_text("0")
        
        score_val = page.locator("#gauge-score").text_content()
        assert int(score_val) > 0
        print(f"[+] UI flow verified. Matching score: {score_val}%")
        
        # 8. Verify that skills badges are populated in the DOM
        matched_badges = page.locator("#matched-skills-container .matched-badge")
        missing_badges = page.locator("#missing-skills-container .missing-badge")
        expect(matched_badges.first).to_be_visible()
        
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
        expect(page.locator("#support-status")).to_have_text("送信済み")
        assert page.locator("#support-status").text_content() == "送信済み"
        
        browser.close()
