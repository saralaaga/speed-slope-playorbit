# -*- coding: utf-8 -*-
"""Offline checks for the generated static site."""
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET


BASE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(BASE, 'app')
STATIC_DIRS = {'about', 'contact', 'dmca', 'hot-games', 'new-games', 'privacy', 'search', 'terms'}


def load_json(name):
    with open(os.path.join(BASE, name), encoding='utf-8') as f:
        return json.load(f)


def selected_games():
    config = load_json('site_config.json')
    games = load_json('games_data.json')
    mode = config.get('launch_mode', 'single')
    if mode == 'single':
        slug = config.get('launch_game_slug') or games[0]['slug']
        return [g for g in games if g['slug'] == slug]
    if mode == 'slugs':
        slugs = set(config.get('published_game_slugs') or [])
        return [g for g in games if g['slug'] in slugs]
    if mode in ('portal', 'all'):
        return games
    raise AssertionError(f'Unknown launch_mode: {mode}')


def assert_no_stale_game_dirs(expected_slugs):
    dirs = {
        name for name in os.listdir(APP)
        if os.path.isdir(os.path.join(APP, name))
        and name not in STATIC_DIRS
        and name not in {'assets', 'games'}
    }
    stale = sorted(dirs - expected_slugs)
    missing = sorted(expected_slugs - dirs)
    assert not stale, f'Stale game directories in app/: {stale}'
    assert not missing, f'Missing game directories in app/: {missing}'


def assert_games_json(expected_slugs):
    data = load_json(os.path.join('app', 'games.json'))
    slugs = {g['slug'] for g in data}
    assert slugs == expected_slugs, f'games.json slugs mismatch: {sorted(slugs ^ expected_slugs)}'


def assert_sitemap(expected_slugs):
    tree = ET.parse(os.path.join(APP, 'sitemap.xml'))
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    locs = [node.text for node in tree.findall('.//sm:loc', ns)]
    paths = {urllib.parse.urlparse(loc).path.strip('/') for loc in locs}
    sitemap_game_slugs = {path for path in paths if path and '/' not in path and path not in STATIC_DIRS}
    assert sitemap_game_slugs == expected_slugs, (
        f'sitemap game slugs mismatch: {sorted(sitemap_game_slugs ^ expected_slugs)}'
    )


def target_exists(base_file, url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme or parsed.netloc or url.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
        return True
    path = urllib.parse.unquote(parsed.path)
    if not path:
        return True
    target = os.path.normpath(os.path.join(os.path.dirname(base_file), path))
    if path.endswith('/'):
        target = os.path.join(target, 'index.html')
    return os.path.exists(target)


def assert_local_links():
    attr = re.compile(r'(?:href|src)="([^"]+)"')
    missing = []
    for root, _, files in os.walk(APP):
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(root, name)
            with open(path, encoding='utf-8') as f:
                for url in attr.findall(f.read()):
                    if not target_exists(path, url):
                        missing.append((os.path.relpath(path, APP), url))
    assert not missing, f'Missing local links/assets: {missing[:20]}'


def main():
    expected_slugs = {g['slug'] for g in selected_games()}
    assert expected_slugs, 'No games selected for publishing'
    assert_no_stale_game_dirs(expected_slugs)
    assert_games_json(expected_slugs)
    assert_sitemap(expected_slugs)
    assert_local_links()
    print(f'OK - validated {len(expected_slugs)} published game(s)')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as exc:
        print(f'FAIL - {exc}', file=sys.stderr)
        sys.exit(1)
