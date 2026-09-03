"""Browser regression guards for the authenticated production shell layout."""

import os
import sys

from playwright.sync_api import sync_playwright


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME


def browser_context(browser, viewport):
    return browser.new_context(
        viewport=viewport,
        http_credentials={
            "username": BASIC_AUTH_USERNAME,
            "password": BASIC_AUTH_PASSWORD,
        },
    )


def test_authenticated_desktop_layout_has_no_document_overflow(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser_context(browser, {"width": 1440, "height": 900})
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")

        metrics = page.evaluate(
            """() => ({
                clientWidth: document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
                authModalActive: document.querySelector('#auth-modal').classList.contains('active'),
                serverAuthMarker: !!document.querySelector('meta[name="mighty-server-authenticated"][content="true"]'),
                selectWidth: document.querySelector('#comparison-job-select').getBoundingClientRect().width
            })"""
        )

        assert metrics["serverAuthMarker"] is True
        assert metrics["authModalActive"] is False
        assert metrics["scrollWidth"] == metrics["clientWidth"]
        assert metrics["selectWidth"] <= 440.5
        context.close()
        browser.close()


def test_all_sidebar_destinations_are_real_views_inside_the_app_shell(fastapi_server):
    routes = [
        "home-view",
        "matching-section",
        "admin-dashboard-section",
        "attendance-section",
        "survey-section",
        "aptitude-demo-section",
        "onboarding-section",
        "training-section",
    ]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser_context(browser, {"width": 1440, "height": 900})
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")

        for target_id in routes:
            href = "#top" if target_id == "home-view" else f"#{target_id}"
            page.locator(f'.sidebar-nav-item[href="{href}"]').click()
            page.wait_for_timeout(75)
            state = page.locator(f"#{target_id}").evaluate(
                """el => ({
                    active: el.classList.contains('tab-active'),
                    visible: getComputedStyle(el).display !== 'none',
                    insideMain: !!el.closest('.global-main-area'),
                    clientWidth: document.documentElement.clientWidth,
                    scrollWidth: document.documentElement.scrollWidth
                })"""
            )
            assert state == {
                "active": True,
                "visible": True,
                "insideMain": True,
                "clientWidth": 1440,
                "scrollWidth": 1440,
            }

        context.close()
        browser.close()


def test_light_theme_uses_readable_content_and_navigation_surfaces(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser_context(browser, {"width": 1440, "height": 900})
        context.add_init_script("window.localStorage.setItem('msb-theme', 'light')")
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")
        page.wait_for_function("() => document.documentElement.dataset.theme === 'light'")

        colors = page.evaluate(
            """() => {
                const panel = document.querySelector('.panel');
                const field = document.querySelector('.textarea-input');
                const sidebarLabel = document.querySelector('[data-i18n="nav_home"]');
                return {
                    panelBackground: getComputedStyle(panel).backgroundColor,
                    panelText: getComputedStyle(panel).color,
                    fieldBackground: getComputedStyle(field).backgroundColor,
                    fieldText: getComputedStyle(field).color,
                    sidebarText: getComputedStyle(sidebarLabel).color
                };
            }"""
        )

        sidebar_channels = [int(value) for value in colors.pop("sidebarText")[4:-1].split(", ")]
        assert colors == {
            "panelBackground": "rgb(255, 255, 255)",
            "panelText": "rgb(15, 23, 42)",
            "fieldBackground": "rgb(248, 250, 252)",
            "fieldText": "rgb(15, 23, 42)",
        }
        assert min(sidebar_channels) >= 200
        context.close()
        browser.close()


def test_authenticated_mobile_layout_and_drawer_are_usable(fastapi_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser_context(browser, {"width": 390, "height": 844})
        page = context.new_page()
        page.route("**/*.mp4", lambda route: route.abort())
        page.goto(fastapi_server, wait_until="domcontentloaded")

        metrics = page.evaluate(
            """() => {
                const sidebar = document.querySelector('#global-sidebar');
                const main = document.querySelector('.global-main-area');
                const inputs = document.querySelector('.hero-inputs-container');
                return {
                    clientWidth: document.documentElement.clientWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    sidebarPosition: getComputedStyle(sidebar).position,
                    sidebarX: sidebar.getBoundingClientRect().x,
                    mainY: main.getBoundingClientRect().y,
                    heroY: document.querySelector('.hero-video-showcase').getBoundingClientRect().y,
                    inputColumns: getComputedStyle(inputs).gridTemplateColumns.split(' ').length,
                    authModalActive: document.querySelector('#auth-modal').classList.contains('active')
                };
            }"""
        )

        assert metrics["scrollWidth"] == metrics["clientWidth"]
        assert metrics["sidebarPosition"] == "fixed"
        assert metrics["sidebarX"] <= -279
        assert metrics["mainY"] <= 80
        assert metrics["heroY"] <= 110
        assert metrics["inputColumns"] == 1
        assert metrics["authModalActive"] is False

        for target_id in [
            "home-view",
            "matching-section",
            "admin-dashboard-section",
            "attendance-section",
            "survey-section",
            "aptitude-demo-section",
            "onboarding-section",
            "training-section",
        ]:
            page.evaluate("target => switchAppTab('#' + target)", target_id)
            widths = page.evaluate(
                "() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]"
            )
            assert widths == [390, 390], f"mobile overflow in {target_id}"

        page.evaluate("switchAppTab('#home-view')")

        page.locator("#mobile-menu-btn").click()
        page.wait_for_timeout(350)
        assert page.locator("#mobile-menu-btn").get_attribute("aria-controls") == "global-sidebar"
        assert page.locator("#mobile-menu-btn").get_attribute("aria-expanded") == "true"
        assert page.locator("#sidebar-backdrop").evaluate("el => el.classList.contains('active')") is True
        assert abs(page.locator("#global-sidebar").bounding_box()["x"]) < 1

        page.locator("#sidebar-backdrop").click(position={"x": 380, "y": 400}, force=True)
        page.wait_for_timeout(350)
        assert page.locator("#mobile-menu-btn").get_attribute("aria-expanded") == "false"
        assert page.locator("#sidebar-backdrop").evaluate("el => el.classList.contains('active')") is False
        context.close()
        browser.close()
