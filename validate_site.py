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
STATIC_DIRS = {'about', 'admin', 'contact', 'dmca', 'hot-games', 'new-games', 'privacy', 'search', 'terms'}


def load_json(name):
    with open(os.path.join(BASE, name), encoding='utf-8') as f:
        return json.load(f)


def load_site_config():
    cms_path = os.path.join(BASE, 'cms-data', 'sites', os.environ.get('SPEEDSLOPE_CMS_SITE', 'speedslope-net') + '.json')
    if os.path.exists(cms_path):
        with open(cms_path, encoding='utf-8') as f:
            return json.load(f)
    return load_json('site_config.json')


def load_games_data():
    cms_dir = os.path.join(BASE, 'cms-data', 'games')
    if os.path.isdir(cms_dir):
        games = []
        for name in os.listdir(cms_dir):
            if name.endswith('.json'):
                with open(os.path.join(cms_dir, name), encoding='utf-8') as f:
                    games.append(json.load(f))
        return sorted(games, key=lambda g: (g.get('sort_order', 999999), g['slug']))
    return load_json('games_data.json')


def selected_games():
    config = load_site_config()
    removed = build_constant('REMOVED_GAME_SLUGS', set())
    games = [g for g in load_games_data() if g['slug'] not in removed]
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
    config = load_site_config()
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
    config = load_site_config()
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


def build_constant(name, default):
    with open(os.path.join(BASE, 'build_site.py'), encoding='utf-8') as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    return default


def assert_featured_category_players():
    featured = build_constant('FEATURED_CATEGORY_GAMES', {})
    removed = build_constant('REMOVED_GAME_SLUGS', set())
    game_urls = {g['slug']: g['url'] for g in load_games_data()}
    missing = []
    for cat, slug in featured.items():
        rel = f'games/{cat}/index.html'
        iframe_src = game_urls.get(slug)
        path = os.path.join(APP, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        if 'class="category-player"' not in html:
            missing.append(rel)
        elif slug not in removed and iframe_src and f'<iframe src="{iframe_src}"' not in html:
            missing.append(rel)
        if html.count('class="game-card"') >= 4 and html.count('class="category-alt-game"') < 3:
            missing.append(rel + ' alternatives')
    assert not missing, f'Missing featured category players: {missing}'


def assert_removed_game_redirects():
    removed_slugs = build_constant('REMOVED_GAME_SLUGS', set())
    removed_categories = build_constant('REMOVED_CATEGORY_REDIRECTS', {})
    published_slugs = {g['slug'] for g in load_json(os.path.join('app', 'games.json'))}
    leaked = sorted(published_slugs & set(removed_slugs))
    assert not leaked, f'Removed games still published: {leaked}'
    with open(os.path.join(APP, '_redirects'), encoding='utf-8') as f:
        redirects = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
    missing = [f'/{slug}/ / 301' for slug in sorted(removed_slugs) if f'/{slug}/ / 301' not in redirects]
    missing += [
        f'/games/{src}/ /games/{dst}/ 301'
        for src, dst in sorted(removed_categories.items())
        if not os.path.exists(os.path.join(APP, 'games', src, 'index.html'))
        and f'/games/{src}/ /games/{dst}/ 301' not in redirects
    ]
    assert not missing, f'Missing removed game/category redirects: {missing[:20]}'


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


def assert_search_preview_signals():
    offenders = []
    for root, _, files in os.walk(APP):
        for name in files:
            if name != 'index.html':
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, APP)
            with open(path, encoding='utf-8') as f:
                html = f.read()
            if '<meta name="robots" content="noindex' in html:
                continue
            if '<meta name="robots" content="index,follow,max-image-preview:large">' not in html:
                offenders.append(rel + ' robots')
            if rel.startswith('games/'):
                if '"@type": "ItemList"' not in html:
                    offenders.append(rel + ' itemlist')
            elif rel.split('/')[0] not in STATIC_DIRS and 'class="stage"' in html:
                if 'class="stage-preview-img"' not in html:
                    offenders.append(rel + ' preview image')
    assert not offenders, f'Missing search preview signals: {offenders[:20]}'


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
    assert_removed_game_redirects()
    assert_sidebar_mini_games_are_images_only()
    assert_search_preview_signals()
    print(f'OK - validated {len(expected_slugs)} published game(s)')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as exc:
        print(f'FAIL - {exc}', file=sys.stderr)
        sys.exit(1)
