---
name: playwright-ui-testing
description: Execute automated Playwright UI tests, visual regression checks, responsive viewport validation, and accessibility (a11y) audits for web applications and landing pages.
triggers:
  - "run ui tests"
  - "test frontend"
  - "playwright test"
  - "visual regression"
license: Apache-2.0
metadata:
  version: v1
  publisher: mighty-link
---

# Playwright UI & Visual Regression Testing Skill

Use this skill to run automated browser testing, cross-browser validation, responsiveness checks, and visual regression tests against the local or deployed landing page.

---

## 1. Quick Test Execution (PowerShell)

```powershell
# 1. Run full Playwright test suite
npx playwright test

# 2. Run with UI mode for debugging
npx playwright test --ui

# 3. Run specific visual regression or demo check
npx playwright test tests/e2e/demo.spec.ts --project=chromium
```

---

## 2. Standard E2E Test Template (`tests/e2e/landing_page.spec.ts`)

```typescript
import { test, expect } from '@playwright/test';

test.describe('Mighty Link AI Connect Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Hero section and CTA button are visible and interactive', async ({ page }) => {
    const heroTitle = page.locator('h1');
    await expect(heroTitle).toBeVisible();

    const ctaButton = page.locator('#main-cta');
    await expect(ctaButton).toBeEnabled();
    await ctaButton.click();
  });

  test('Responsive viewport test (Mobile & Desktop)', async ({ page }) => {
    // Test Mobile Viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('nav')).toBeVisible();

    // Test Desktop Viewport
    await page.setViewportSize({ width: 1440, height: 900 });
    await expect(page.locator('nav')).toBeVisible();
  });
});
```

---

## 3. Visual Regression & Screenshot Capture

Capture visual baselines to prevent UI layout shifts:

```powershell
# Update snapshot baselines after intentional UI design changes
npx playwright test --update-snapshots
```
