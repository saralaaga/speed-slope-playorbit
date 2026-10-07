#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python port of check_game_availability.js (npm playwright unavailable).

Usage: SITE_BASE_URL=http://127.0.0.1:8000 <uv-playwright-python> check_availability_py.py slug1 slug2 ...
"""
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get('SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
REQUESTED = set(sys.argv[1:])
GAMES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'games.json')
BLOCKED_TEXT = re.compile(r'not available here|click here to play|game is not available', re.I)
BLOCKED_URL = re.compile(r'blocked\.html|unregistered=true|chrome-error://chromewebdata', re.I)


def frame_text(page):
    chunks = []
    for frame in page.frames:
        try:
            chunks.append(frame.locator('body').inner_text(timeout=1500))
        except Exception:
            pass
    return re.sub(r'\s+', ' ', '\n'.join(chunks)).strip()


def check_game(browser, game):
    url = f"{BASE}/{game['url']}"
    last_error = ''
    for _attempt in range(2):
        page = browser.new_page(viewport={'width': 1280, 'height': 720})
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            try:
                page.click('#playNow', timeout=3000)
            except Exception:
                pass
            page.wait_for_timeout(5000)
            for frame in page.frames:
                if frame is page.main_frame:
                    continue
                try:
                    frame.get_by_text('^(play|play now)$', exact=False).first.click(timeout=2000)
                except Exception:
                    pass
            page.wait_for_timeout(5000)
            text = frame_text(page)
            frame_urls = '\n'.join(f.url for f in page.frames)
            blocked = bool(BLOCKED_TEXT.search(text)) or bool(BLOCKED_URL.search(frame_urls))
            return game['slug'], (not blocked), ('blocked/unavailable iframe' if blocked else '')
        except Exception as err:
            last_error = str(err).split('\n')[0]
        finally:
            try:
                page.close()
            except Exception:
                pass
    return game['slug'], False, last_error


def main():
    with open(GAMES_JSON, encoding='utf-8') as f:
        games = [g for g in json.load(f) if not REQUESTED or g['slug'] in REQUESTED]
    bad = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for game in games:
                slug, ok, detail = check_game(browser, game)
                print(f"{'OK' if ok else 'FAIL'} {slug}{' ' + detail if detail else ''}", flush=True)
                if not ok:
                    bad.append(slug)
        finally:
            browser.close()
    if bad:
        print(f"Blocked/unavailable games: {', '.join(bad)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
