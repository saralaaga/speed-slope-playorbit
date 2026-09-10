#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const baseUrl = process.env.SITE_BASE_URL || 'http://127.0.0.1:8000';
const requested = new Set(process.argv.slice(2));
const concurrency = Number(process.env.CHECK_CONCURRENCY || 1);
const games = JSON.parse(fs.readFileSync(path.join(__dirname, 'app', 'games.json'), 'utf8'))
  .filter((game) => !requested.size || requested.has(game.slug));

const BLOCKED_TEXT = /not available here|click here to play|game is not available/i;

async function frameText(page) {
  const chunks = [];
  for (const frame of page.frames()) {
    try {
      chunks.push(await frame.locator('body').innerText({ timeout: 1500 }));
    } catch (_) {}
  }
  return chunks.join('\n').replace(/\s+/g, ' ').trim();
}

async function checkGame(browser, game) {
  const url = `${baseUrl.replace(/\/$/, '')}/${game.url}`;
  let lastError = '';
  for (let attempt = 1; attempt <= 2; attempt++) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.click('#playNow', { timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(5000);
      for (const frame of page.frames()) {
        if (frame === page.mainFrame()) continue;
        await frame.getByText(/^(play|play now)$/i).first().click({ timeout: 2000 }).catch(() => {});
      }
      await page.waitForTimeout(5000);
      const text = await frameText(page);
      const frameUrls = page.frames().map((frame) => frame.url()).join('\n');
      const blocked = BLOCKED_TEXT.test(text) || /blocked\.html|unregistered=true|chrome-error:\/\/chromewebdata/i.test(frameUrls);
      return { game, ok: !blocked, detail: blocked ? 'blocked/unavailable iframe' : '' };
    } catch (err) {
      lastError = err.message.split('\n')[0];
    } finally {
      await page.close().catch(() => {});
    }
  }
  return { game, ok: false, detail: lastError };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const bad = [];
  let cursor = 0;
  async function worker() {
    while (cursor < games.length) {
      const game = games[cursor++];
      const result = await checkGame(browser, game);
      console.log(`${result.ok ? 'OK' : 'FAIL'} ${game.slug}${result.detail ? ' ' + result.detail : ''}`);
      if (!result.ok) bad.push(game.slug);
    }
  }
  await Promise.all(Array.from({ length: Math.max(1, concurrency) }, worker));
  await browser.close();
  if (bad.length) {
    console.error(`Blocked/unavailable games: ${bad.join(', ')}`);
    process.exit(1);
  }
})();
