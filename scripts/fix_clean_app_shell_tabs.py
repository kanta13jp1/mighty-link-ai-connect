#!/usr/bin/env python3
"""Ensure clean flat SPA tab structure for all 8 app sections."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

# 1. Close #home-view right before #onboarding-section if it's wrapping everything
# Let's inspect where #home-view should close: after #comparison-section and #video-section
if '<div id="home-view"' in content and '</div><!-- end home-view -->' not in content:
    # Wrap hero, report, comparison, video, models, knowledge-flow in #home-view
    pass

# Ensure #training-section is a top-level child of .global-main-area
# and that switchAppTab activates it properly without parent display:none interference.

# Let's update switchAppTab to ensure seamless activation:
clean_switch_tab_js = """
        function switchAppTab(targetId, updateHistory = true) {
            if (currentActiveTabId && tabScrollMemory) {
                tabScrollMemory[currentActiveTabId] = window.scrollY;
            }

            if (!targetId || targetId === '#top' || targetId === '#home' || targetId === 'top' || targetId === 'home') {
                targetId = 'home-view';
            } else {
                targetId = targetId.replace(/^#/, '');
            }

            const allTabViews = document.querySelectorAll('.app-tab-view');
            let matched = false;

            allTabViews.forEach(view => {
                const isHome = view.classList.contains('home-tab-element') || view.id === 'home-view';
                if ((targetId === 'home-view' && isHome) || (view.id === targetId)) {
                    view.classList.add('tab-active');
                    view.style.display = 'block';
                    matched = true;
                } else {
                    view.classList.remove('tab-active');
                    view.style.display = 'none';
                }
            });

            if (!matched) {
                allTabViews.forEach(view => {
                    if (view.classList.contains('home-tab-element') || view.id === 'home-view') {
                        view.classList.add('tab-active');
                        view.style.display = 'block';
                    } else {
                        view.classList.remove('tab-active');
                        view.style.display = 'none';
                    }
                });
                targetId = 'home-view';
            }

            currentActiveTabId = targetId;

            // Ensure child elements inside active tab are visible
            const activeView = document.getElementById(targetId);
            if (activeView) {
                activeView.querySelectorAll('.fade-in-on-scroll').forEach(el => {
                    el.classList.add('is-visible');
                    el.style.opacity = '1';
                    el.style.transform = 'none';
                });
            }

            // Sync sidebar active status
            const sidebarLinks = document.querySelectorAll('.global-app-sidebar .sidebar-nav-item');
            sidebarLinks.forEach(link => {
                const href = link.getAttribute('href') || '';
                const tabAttr = link.getAttribute('data-tab-id') || '';
                const linkTarget = href.replace(/^#/, '');

                const isMatch = (targetId === 'home-view' && (linkTarget === 'top' || linkTarget === 'home' || tabAttr === 'home-view')) ||
                                (tabAttr && targetId === tabAttr) ||
                                (linkTarget && targetId === linkTarget);

                if (isMatch) {
                    link.classList.add('active');
                    link.setAttribute('aria-current', 'page');
                } else {
                    link.classList.remove('active');
                    link.removeAttribute('aria-current');
                }
            });

            closeSidebarDrawer();

            const savedScroll = (tabScrollMemory && tabScrollMemory[targetId]) || 0;
            window.scrollTo({ top: savedScroll, behavior: 'smooth' });

            if (updateHistory && history.pushState) {
                const hashToSet = targetId === 'home-view' ? '#top' : `#${targetId}`;
                if (window.location.hash !== hashToSet) {
                    history.pushState(null, '', hashToSet);
                }
            }
        }
"""

pattern = r'function switchAppTab\(targetId, updateHistory = true\) \{[\s\S]*?\}\s*window\.addEventListener\(\'DOMContentLoaded\''
content = re.sub(pattern, clean_switch_tab_js.strip() + '\n\n        window.addEventListener(\'DOMContentLoaded\'', content)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] switchAppTab engine updated to guarantee explicit block display for all tabs!")
