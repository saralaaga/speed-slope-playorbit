# -*- coding: utf-8 -*-
"""Offline checks for the generated static site."""
import ast
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


def home_game_slug():
    config = load_json('site_config.json')
    games = selected_games()
    slug = config.get('home_game_slug') or config.get('launch_game_slug') or games[0]['slug']
    assert slug in {g['slug'] for g in games}, f'home_game_slug not selected for publishing: {slug}'
    return slug


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
    # In single mode the home page is the play page and /slug/ only redirects
    # there (noindex), so game slugs are intentionally absent from the sitemap.
    config = load_json('site_config.json')
    if config.get('launch_mode', 'single') == 'single':
        expected_slugs = set()
    else:
        expected_slugs = set(expected_slugs)
        expected_slugs.discard(home_game_slug())
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


def assert_nav_dropdown_hover_bridge():
    with open(os.path.join(APP, 'assets', 'css', 'style.css'), encoding='utf-8') as f:
        css = f.read()
    assert '.nav-drop:hover::after' in css, 'Categories dropdown gap needs a hover bridge'


def assert_car_racing_has_no_card_games():
    games = load_json(os.path.join('app', 'games.json'))
    bad = [g['slug'] for g in games if 'Car Racing Games' in g['categories'] and 'Card Games' in g['categories']]
    assert not bad, f'Card games listed under Car Racing Games: {bad}'


def assert_golf_games_are_not_io_games():
    games = load_json(os.path.join('app', 'games.json'))
    bad = [g['slug'] for g in games if 'Golf Games' in g['categories'] and 'IO Games' in g['categories']]
    assert not bad, f'Golf games listed under IO Games: {bad}'


def assert_categories_have_enough_games(min_count=1):
    counts = {}
    for g in load_json(os.path.join('app', 'games.json')):
        for cat in g['categories']:
            counts[cat] = counts.get(cat, 0) + 1
    thin = {cat: count for cat, count in counts.items() if count < min_count}
    assert not thin, f'Categories with fewer than {min_count} games: {thin}'


def assert_featured_category_players():
    with open(os.path.join(BASE, 'build_site.py'), encoding='utf-8') as f:
        tree = ast.parse(f.read())
    featured = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'FEATURED_CATEGORY_GAMES' for t in node.targets):
            featured = ast.literal_eval(node.value)
            break
    game_urls = {g['slug']: g['url'] for g in load_json('games_data.json')}
    missing = []
    for cat, slug in featured.items():
        rel = f'games/{cat}/index.html'
        iframe_src = game_urls.get(slug)
        path = os.path.join(APP, rel)
        if not os.path.exists(path):
            continue
        if not iframe_src:
            missing.append(rel)
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        if 'class="category-player"' not in html or f'<iframe src="{iframe_src}"' not in html:
            missing.append(rel)
        if html.count('class="game-card"') >= 4 and html.count('class="category-alt-game"') < 3:
            missing.append(rel + ' alternatives')
    assert not missing, f'Missing featured category players: {missing}'


def assert_sidebar_mini_games_are_images_only():
    offenders = []
    for root, _, files in os.walk(APP):
        for name in files:
            if name != 'index.html':
                continue
            path = os.path.join(root, name)
            with open(path, encoding='utf-8') as f:
                html = f.read()
            if 'class="mini-game"' in html and 'class="t"' in html:
                offenders.append(os.path.relpath(path, APP))
    assert not offenders, f'Sidebar mini games still render text labels: {offenders[:20]}'


def main():
    expected_slugs = {g['slug'] for g in selected_games()}
    assert expected_slugs, 'No games selected for publishing'
    assert_no_stale_game_dirs(expected_slugs)
    assert_games_json(expected_slugs)
    assert_sitemap(expected_slugs)
    assert_local_links()
    assert_nav_dropdown_hover_bridge()
    assert_car_racing_has_no_card_games()
    assert_golf_games_are_not_io_games()
    assert_categories_have_enough_games()
    assert_featured_category_players()
    assert_sidebar_mini_games_are_images_only()
    print(f'OK - validated {len(expected_slugs)} published game(s)')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as exc:
        print(f'FAIL - {exc}', file=sys.stderr)
        sys.exit(1)
