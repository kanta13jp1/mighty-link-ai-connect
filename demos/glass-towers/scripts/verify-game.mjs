import fs from "node:fs/promises";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { PNG } from "pngjs";

const port = 4187;
const baseUrl = `http://127.0.0.1:${port}`;
const projectDir = fileURLToPath(new URL("../", import.meta.url));
const artifacts = new URL("../artifacts/", import.meta.url);
await fs.mkdir(artifacts, { recursive: true });

const server = spawn(process.execPath, ["./node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", String(port), "--strictPort"], {
  cwd: projectDir,
  stdio: ["ignore", "pipe", "pipe"],
});

function waitForServer() {
  return new Promise((resolve, reject) => {
    const startedAt = Date.now();
    const poll = async () => {
      if (server.exitCode !== null) {
        reject(new Error(`Vite exited early with ${server.exitCode}`));
        return;
      }
      try {
        const response = await fetch(baseUrl);
        if (response.ok) {
          resolve();
          return;
        }
      } catch {
        // The server is still starting.
      }
      if (Date.now() - startedAt > 15000) {
        reject(new Error("Vite server did not start"));
        return;
      }
      setTimeout(poll, 150);
    };
    poll();
  });
}

async function waitForScore(page, score) {
  try {
    await page.waitForFunction((target) => window.__GLASS_TOWERS__?.snapshot().score >= target, score, { timeout: 9000 });
  } catch (error) {
    const snapshot = await page.evaluate(() => window.__GLASS_TOWERS__?.snapshot());
    throw new Error(`Score ${score} timed out: ${JSON.stringify(snapshot)}`, { cause: error });
  }
}

async function inspectPixels(buffer) {
  const png = PNG.sync.read(buffer);
  const colors = new Set();
  let bright = 0;
  let dark = 0;
  for (let y = 0; y < png.height; y += 12) {
    for (let x = 0; x < png.width; x += 12) {
      const offset = (png.width * y + x) * 4;
      const red = png.data[offset];
      const green = png.data[offset + 1];
      const blue = png.data[offset + 2];
      colors.add(`${Math.round(red / 16)}-${Math.round(green / 16)}-${Math.round(blue / 16)}`);
      const luminance = (red + green + blue) / 3;
      if (luminance > 210) bright += 1;
      if (luminance < 90) dark += 1;
    }
  }
  if (colors.size < 35 || bright === 0 || dark === 0) {
    throw new Error(`Canvas screenshot appears blank or flat: colors=${colors.size}, bright=${bright}, dark=${dark}`);
  }
  return { colors: colors.size, bright, dark };
}

const browser = await chromium.launch({
  headless: true,
  args: [
    "--use-angle=vulkan",
    "--enable-features=Vulkan",
    "--disable-vulkan-surface",
    "--enable-unsafe-webgpu",
  ],
});
const consoleErrors = [];
const results = {};

try {
  await waitForServer();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__GLASS_TOWERS__?.snapshot().state === "aiming");
  results.desktopEngine = await page.evaluate(() => window.__GLASS_TOWERS__.snapshot().engine);
  if (results.desktopEngine.physics !== "rapier-wasm") throw new Error("Rapier WASM did not initialize");
  if (!/^0\.20\./.test(results.desktopEngine.physicsVersion)) throw new Error("Unexpected Rapier version");
  if (!["webgpu", "webgl2"].includes(results.desktopEngine.renderer)) throw new Error("Unexpected renderer backend");

  const beforeMove = await page.evaluate(() => window.__GLASS_TOWERS__.snapshot());
  await page.mouse.move(1090, 430);
  await page.waitForTimeout(300);
  const afterMove = await page.evaluate(() => window.__GLASS_TOWERS__.snapshot());
  if (afterMove.aimX === beforeMove.aimX || Math.abs(afterMove.displayAimX) < 0.2) {
    throw new Error("Mouse movement did not move the aiming piece");
  }

  await page.evaluate(() => window.__GLASS_TOWERS__.restart());
  await page.mouse.click(720, 430);
  await page.evaluate(() => window.__GLASS_TOWERS__.advance(600));
  await waitForScore(page, 1);
  await page.waitForFunction(() => window.__GLASS_TOWERS__.snapshot().state === "aiming");
  await page.evaluate(() => window.__GLASS_TOWERS__.dropAt(0));
  await page.evaluate(() => window.__GLASS_TOWERS__.advance(600));
  await waitForScore(page, 2);
  results.stableRun = await page.evaluate(() => window.__GLASS_TOWERS__.snapshot());

  await page.evaluate(() => window.__GLASS_TOWERS__.restart());
  await page.evaluate(() => window.__GLASS_TOWERS__.dropAt(3.15));
  await page.evaluate(() => window.__GLASS_TOWERS__.advance(600));
  await page.waitForFunction(() => window.__GLASS_TOWERS__.snapshot().state === "gameover", null, { timeout: 9000 });
  results.failedRun = await page.evaluate(() => window.__GLASS_TOWERS__.snapshot());
  const gameOverScreenshot = await page.screenshot({ path: fileURLToPath(new URL("glass-towers-game-over.png", artifacts)) });
  results.gameOverPixels = await inspectPixels(gameOverScreenshot);
  results.gameOverLayout = await page.locator("#game-over").evaluate((element) => element.getBoundingClientRect().toJSON());
  await page.locator("#play-again-button").click();
  await page.waitForFunction(() => window.__GLASS_TOWERS__.snapshot().state === "aiming" && window.__GLASS_TOWERS__.snapshot().score === 0);

  await page.keyboard.press("Space");
  await page.evaluate(() => window.__GLASS_TOWERS__.advance(600));
  await waitForScore(page, 1);
  results.keyboardRun = await page.evaluate(() => window.__GLASS_TOWERS__.snapshot());

  const desktopScreenshot = await page.screenshot({ path: fileURLToPath(new URL("glass-towers-desktop.png", artifacts)) });
  results.desktopPixels = await inspectPixels(desktopScreenshot);
  results.desktopLayout = await page.evaluate(() => ({
    width: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    canvas: document.querySelector("#game-canvas").getBoundingClientRect().toJSON(),
    next: document.querySelector(".next-piece").getBoundingClientRect().toJSON(),
  }));

  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    hasTouch: true,
    isMobile: true,
  });
  const mobile = await mobileContext.newPage();
  mobile.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(`mobile: ${message.text()}`);
  });
  mobile.on("pageerror", (error) => consoleErrors.push(`mobile: ${error.message}`));
  await mobile.goto(`${baseUrl}?renderer=webgl2`, { waitUntil: "networkidle" });
  await mobile.waitForFunction(() => window.__GLASS_TOWERS__?.snapshot().state === "aiming");
  results.mobileEngine = await mobile.evaluate(() => window.__GLASS_TOWERS__.snapshot().engine);
  if (results.mobileEngine.renderer !== "webgl2") throw new Error("Forced WebGL 2 fallback was not selected");
  if (results.mobileEngine.physics !== "rapier-wasm") throw new Error("Mobile Rapier WASM did not initialize");
  await mobile.touchscreen.tap(195, 390);
  await mobile.evaluate(() => window.__GLASS_TOWERS__.advance(600));
  await waitForScore(mobile, 1);
  const mobileScreenshot = await mobile.screenshot({ path: fileURLToPath(new URL("glass-towers-mobile.png", artifacts)) });
  results.mobilePixels = await inspectPixels(mobileScreenshot);
  results.mobileLayout = await mobile.evaluate(() => ({
    width: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    height: document.documentElement.clientHeight,
    scrollHeight: document.documentElement.scrollHeight,
    gameOverHidden: document.querySelector("#game-over").hidden,
  }));
  await mobileContext.close();

  if (results.desktopLayout.scrollWidth !== results.desktopLayout.width) throw new Error("Desktop has horizontal overflow");
  if (results.gameOverLayout.left < 0 || results.gameOverLayout.right > results.desktopLayout.width) throw new Error("Game-over panel is outside the viewport");
  if (results.mobileLayout.scrollWidth !== results.mobileLayout.width) throw new Error("Mobile has horizontal overflow");
  if (results.mobileLayout.scrollHeight !== results.mobileLayout.height) throw new Error("Mobile viewport scrolls");
  if (consoleErrors.length) throw new Error(`Console errors: ${consoleErrors.join(" | ")}`);

  await fs.writeFile(new URL("verification.json", artifacts), `${JSON.stringify({ ...results, consoleErrors }, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ passed: true, ...results, consoleErrors }, null, 2));
} finally {
  await browser.close();
  server.kill("SIGTERM");
}
