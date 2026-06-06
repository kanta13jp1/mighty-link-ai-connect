#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automated screen capture script for Mighty Skill-Bridge.
Uses Playwright to capture screenshots of the landing page, analysis report,
comparison board, admin dashboard, and Google WBS spreadsheet.
"""

import argparse
import os
import sys
import time
import subprocess
import httpx
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "exports" / "knowledge_flow" / "screenshots"

def check_server_running(url: str) -> bool:
    try:
        r = httpx.get(url, timeout=2.0)
        return r.status_code == 200
    except httpx.RequestError:
        return False

def main():
    parser = argparse.ArgumentParser(description="Capture screenshots of Mighty Skill-Bridge screens.")
    parser.add_argument(
        "--url",
        default="https://kanta13jp1.github.io/mighty-link-ai-connect/",
        help="App landing page URL to screenshot."
    )
    parser.add_argument(
        "--admin-url",
        default="http://127.0.0.1:8085/admin",
        help="Admin dashboard URL to screenshot."
    )
    parser.add_argument(
        "--sheet-url",
        default="https://docs.google.com/spreadsheets/d/1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8",
        help="Google Sheets WBS URL to screenshot."
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for screenshots."
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Do not start local uvicorn FastAPI server subprocess if unreachable."
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"[*] Saving screenshots to: {output_path.resolve()}")

    server_process = None
    admin_port = 8085

    # Check if local server is needed and start if not running
    if "127.0.0.1" in args.admin_url or "localhost" in args.admin_url:
        # Extract port from admin-url
        try:
            port_part = args.admin_url.split(":")[-1].split("/")[0]
            admin_port = int(port_part)
        except ValueError:
            pass

        health_url = f"http://127.0.0.1:{admin_port}/api/health"
        if not check_server_running(health_url):
            if args.no_server:
                print(f"[!] Local server is not running on port {admin_port} and --no-server is set. Admin panel screenshot may fail.")
            else:
                print(f"[*] Local server not running. Starting uvicorn FastAPI server on port {admin_port}...")
                server_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(admin_port)],
                    cwd=str(PROJECT_ROOT / "src"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # Wait for server ready
                for _ in range(30):
                    if check_server_running(health_url):
                        print(f"[+] Local server started successfully on port {admin_port}.")
                        break
                    time.sleep(0.5)
                else:
                    print(f"[-] Failed to start local uvicorn server on port {admin_port}. Stdout/Stderr in logs.")

    try:
        with sync_playwright() as p:
            print("[*] Launching Chromium browser (headless)...")
            browser = p.chromium.launch(headless=True)
            
            # Setup context with large viewport
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                # Basic Auth credentials for admin dashboard
                http_credentials={"username": "admin", "password": "mighty-link-pass"}
            )
            page = context.new_page()
            page.set_default_timeout(20000) # Safeguard: 20s default timeout for all actions to prevent indefinite hanging

            # --- SCREENSHOT 1: Landing Page ---
            try:
                print(f"[*] Navigating to landing page: {args.url}")
                page.goto(args.url, wait_until="load")
                page.wait_for_timeout(2000) # Let page settle
                
                # Check if public url is not loaded, wait for main title
                page.wait_for_selector("text=Mighty Skill-Bridge", timeout=5000)
                
                shot1 = output_path / "01_landing.png"
                page.screenshot(path=str(shot1), full_page=False)
                print(f"[+] Capture successful: {shot1.name}")
            except Exception as e:
                print(f"[-] Failed to capture landing page: {e}")

            # --- SCREENSHOT 2: Analysis Report ---
            try:
                print("[*] Simulating AI analysis flow...")
                # Click Load Sample buttons
                page.locator(".sample-btn", has_text="Load Sample").nth(0).click()
                page.locator(".sample-btn", has_text="Load Sample").nth(1).click()
                
                # Run analysis
                page.locator("button.big-btn").click()
                
                # Wait for report section to be active and populated
                page.wait_for_selector("#report-section.active", timeout=10000)
                page.wait_for_function("document.getElementById('gauge-score').textContent !== '0'")
                print("[*] Waiting for report animations (3s)...")
                page.wait_for_timeout(3000) # Settle animations
                
                # Focus/scroll to report container
                page.locator("#report-section").scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                
                shot2 = output_path / "02_analysis_report.png"
                page.screenshot(path=str(shot2), full_page=False)
                print(f"[+] Capture successful: {shot2.name}")
            except Exception as e:
                print(f"[-] Failed to simulate and capture analysis report: {e}")

            # --- SCREENSHOT 3: Comparison Board ---
            try:
                print("[*] Scrolling to Comparison Board...")
                page.locator("#comparison-section").scroll_into_view_if_needed()
                page.wait_for_timeout(1000) # Settle scroll
                
                shot3 = output_path / "03_comparison_board.png"
                page.screenshot(path=str(shot3), full_page=False)
                print(f"[+] Capture successful: {shot3.name}")
            except Exception as e:
                print(f"[-] Failed to capture Comparison Board: {e}")

            # --- SCREENSHOT 4: Admin Dashboard ---
            try:
                print(f"[*] Navigating to admin dashboard: {args.admin_url}")
                page.goto(args.admin_url, wait_until="load")
                page.wait_for_timeout(2000)
                
                # Wait for admin content
                page.wait_for_selector("text=External API Guard", timeout=5000)
                
                shot4 = output_path / "04_admin_dashboard.png"
                page.screenshot(path=str(shot4), full_page=False)
                print(f"[+] Capture successful: {shot4.name}")
            except Exception as e:
                print(f"[-] Failed to capture admin dashboard: {e}")

            # --- SCREENSHOT 5: Google WBS Sheets ---
            try:
                print(f"[*] Navigating to WBS Google Sheets: {args.sheet_url}")
                try:
                    page.goto(args.sheet_url, wait_until="domcontentloaded", timeout=15000)
                except Exception as ex:
                    print(f"[!] Sheets navigation warning/timeout: {ex}. Checking current URL...")
                
                # Check if redirected to sign in / login page
                current_url = page.url
                if "accounts.google.com" in current_url or "signin" in current_url or "login" in current_url:
                    print("[!] Redirected to Google Sign-In page. Skipping WBS Google Sheets screenshot.")
                else:
                    print("[*] Waiting for Google Sheets grid rendering (8s)...")
                    page.wait_for_timeout(8000) # Sheets are heavy to load
                    
                    # Bypass font loading wait by overriding font-family to standard system fonts
                    try:
                        page.evaluate("() => { const s = document.createElement('style'); s.innerHTML = '* { font-family: Arial, sans-serif !important; }'; document.head.appendChild(s); }")
                        print("[*] Injected font override style.")
                    except Exception as ex:
                        print(f"[!] Font override injection failed: {ex}")
                    
                    shot5 = output_path / "05_google_sheets_wbs.png"
                    page.screenshot(path=str(shot5), full_page=False, timeout=10000)
                    print(f"[+] Capture successful: {shot5.name}")
            except Exception as e:
                print(f"[-] Failed to capture Google Sheets: {e}")

            browser.close()
            print("[*] Playwright walkthrough complete.")
            
    finally:
        if server_process:
            print("[*] Stopping local uvicorn FastAPI server subprocess...")
            server_process.terminate()
            server_process.wait()
            print("[+] Local server stopped.")

if __name__ == "__main__":
    main()
