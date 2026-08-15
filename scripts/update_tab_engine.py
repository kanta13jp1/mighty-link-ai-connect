#!/usr/bin/env python3
"""Update switchAppTab engine to perfectly manage global sidebar and view routing."""

from pathlib import Path
import re

INDEX_PATH = Path("index.html")
content = INDEX_PATH.read_text(encoding="utf-8")

tab_engine_js = """
        // ==========================================================================
        // UNIFIED GLOBAL SAAS TABBED ROUTING ENGINE
        // ==========================================================================
        function switchAppTab(targetId, updateHistory = true) {
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
                    matched = true;
                } else {
                    view.classList.remove('tab-active');
                }
            });

            if (!matched) {
                allTabViews.forEach(view => {
                    if (view.classList.contains('home-tab-element') || view.id === 'home-view') {
                        view.classList.add('tab-active');
                    } else {
                        view.classList.remove('tab-active');
                    }
                });
                targetId = 'home-view';
            }

            // Synchronize Global Sidebar Navigation Items
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
                } else {
                    link.classList.remove('active');
                }
            });

            // Synchronize Mobile Bottom Navigation
            const mobileLinks = document.querySelectorAll('.mobile-nav-link');
            mobileLinks.forEach(link => {
                const href = link.getAttribute('href') || '';
                const linkTarget = href.replace(/^#/, '');
                if ((targetId === 'home-view' && (linkTarget === 'top' || linkTarget === 'home')) ||
                    (linkTarget && targetId === linkTarget)) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });

            window.scrollTo({ top: 0, behavior: 'smooth' });

            if (updateHistory && history.pushState) {
                const hashToSet = targetId === 'home-view' ? '#top' : `#${targetId}`;
                if (window.location.hash !== hashToSet) {
                    history.pushState(null, '', hashToSet);
                }
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            const initialHash = window.location.hash || '#top';
            switchAppTab(initialHash, false);

            // Intercept navigation clicks globally
            document.addEventListener('click', (e) => {
                const targetLink = e.target.closest('a[href^="#"]');
                if (targetLink && !targetLink.hasAttribute('onclick')) {
                    const href = targetLink.getAttribute('href');
                    if (href && href !== '#' && !href.startsWith('#training-modal')) {
                        e.preventDefault();
                        switchAppTab(href, true);
                    }
                }
            });
        });

        window.addEventListener('hashchange', () => {
            switchAppTab(window.location.hash || '#top', false);
        });
"""

# Replace switchAppTab block
pattern = r'// ==========================================================================\s*// Tabbed SPA Multi-Page View Switching Engine[\s\S]*?window\.addEventListener\(\'hashchange\', \(\) => \{\s*switchAppTab\(window\.location\.hash \|\| \'#top\', false\);\s*\}\);'
content = re.sub(pattern, tab_engine_js.strip(), content)

INDEX_PATH.write_text(content, encoding="utf-8")
print("[SUCCESS] Routing engine updated for Global Sidebar!")
