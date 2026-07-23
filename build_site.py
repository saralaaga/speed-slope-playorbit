# -*- coding: utf-8 -*-
"""PlayOrbit static portal generator.

Reads the full game catalog, publishes the configured subset, and emits HTML
pages, thumbnails, games.json, sitemap.xml and robots.txt into ./app.
"""
import json, os, html, hashlib, colorsys, datetime, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, 'app')
CONFIG_PATH = os.path.join(BASE, 'site_config.json')
DATA_PATH = os.path.join(BASE, 'games_data.json')

DEFAULT_CONFIG = {
    'site_name': 'PlayOrbit',
    'site_url': 'https://www.playorbit.example',
    'tagline': 'Free online games, no downloads - play instantly in your browser.',
    'launch_mode': 'single',
    'launch_game_slug': '',
    'contact_email': 'hello@playorbit.example',
    'games_email': 'games@playorbit.example',
    'legal_email': 'legal@playorbit.example',
    'ads_enabled': False,
    'include_aggregate_rating_schema': False,
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, encoding='utf-8') as f:
        user_config = json.load(f)
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    config['site_url'] = config['site_url'].rstrip('/')
    return config

CONFIG = load_config()
SITE_NAME = CONFIG['site_name']
SITE_URL = CONFIG['site_url']
TAGLINE = CONFIG['tagline']
CONTACT_EMAIL = CONFIG['contact_email']
GAMES_EMAIL = CONFIG['games_email']
LEGAL_EMAIL = CONFIG['legal_email']
TODAY = '2026-07-22'

ALL_CATS = {
    'basketball': ('Basketball Games', 'Dunk, shoot and score in the best free basketball games you can play right in your browser — from realistic shootouts to chaotic random physics matches.'),
    'sports':     ('Sports Games', 'Soccer, cricket, tennis, archery, pool and more — free sports games with instant browser play, no downloads and no sign-ups.'),
    'racing':     ('Racing Games', 'Drift, drive and battle your way to the finish line. Free racing and driving games playable instantly on desktop and mobile.'),
    'puzzle':     ('Puzzle Games', 'Give your brain a workout with free puzzle games — classic logic, match-3, tile merging and bubble popping fun.'),
    'arcade':     ('Arcade Games', 'Fast, addictive arcade games. One more run is never enough — play free arcade hits instantly in your browser.'),
    '2-player':   ('2 Player Games', 'Grab a friend and share the keyboard. The best free 2 player games for same-screen battles, races and random physics chaos.'),
    'io':         ('IO Games', 'Jump into free .io games and compete against players from around the world — territory, karts and arena shooters.'),
    'classics':   ('Classic Games', 'Timeless classics re-made for the browser: 2048, Minesweeper, Mahjong, Pool and more — free and instant.'),
}

CAT_DOT = {
    'basketball': '#ff9f43', 'sports': '#3ddc84', 'racing': '#ff5d5d', 'puzzle': '#b98cff',
    'arcade': '#4dc3ff', '2-player': '#ffd93d', 'io': '#ff6ec7', 'classics': '#9aa78b',
}

def select_games(all_games):
    mode = CONFIG.get('launch_mode', 'single')
    if mode == 'single':
        slug = CONFIG.get('launch_game_slug') or all_games[0]['slug']
        games = [g for g in all_games if g['slug'] == slug]
        if not games:
            raise ValueError(f'launch_game_slug not found in games_data.json: {slug}')
        return games
    if mode == 'slugs':
        slugs = set(CONFIG.get('published_game_slugs') or [])
        games = [g for g in all_games if g['slug'] in slugs]
        missing = sorted(slugs - {g['slug'] for g in games})
        if missing:
            raise ValueError(f'published_game_slugs missing from games_data.json: {missing}')
        return games
    if mode in ('portal', 'all'):
        return all_games
    raise ValueError(f'Unknown launch_mode: {mode}')

# slug, title, iframe URL, categories[0]=primary, tags, rating, plays, hot, new,
# added, description, howto[], controls[(key, action)], tips[]
ALL_GAMES = json.load(open(DATA_PATH, encoding='utf-8'))
G = select_games(ALL_GAMES)
ACTIVE_CAT_KEYS = {c for g in G for c in g['cats']}
CATS = {k: v for k, v in ALL_CATS.items() if k in ACTIVE_CAT_KEYS}

# ============================================================ helpers
def esc(s): return html.escape(str(s), quote=True)

def fmt_plays(n):
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000: return f'{n/1_000:.1f}'.rstrip('0').rstrip('.') + 'K'
    return str(n)

BY_SLUG = {g['slug']: g for g in G}

def game_url(g, pre): return f'{pre}{g["slug"]}/'
def cat_url(c, pre): return f'{pre}games/{c}/'
def thumb_url(g, pre): return f"{pre}assets/thumbs/{g.get('thumbfile', g['slug'] + '.svg')}"

# ============================================================ thumbnails
def palette(slug):
    h = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)
    hue = (h % 360)
    sat = 62 + (h >> 8) % 22
    l1 = 46 + (h >> 16) % 10
    h2 = (hue + 40 + (h >> 20) % 60) % 360
    c1 = colorsys.hls_to_rgb(hue / 360, l1 / 100, sat / 100)
    c2 = colorsys.hls_to_rgb(h2 / 360, (l1 - 12) / 100, min(sat + 8, 95) / 100)
    f = lambda c: '#%02x%02x%02x' % tuple(round(x * 255) for x in c)
    return f(c1), f(c2)

def initials(title):
    if title[0].isdigit(): return title[:4]
    ws = [w for w in title.replace('.', ' ').split() if w]
    return ''.join(w[0] for w in ws[:2]).upper()

MOTIFS = {
    'racing':   '<rect x="-120" y="120" width="900" height="58" rx="29" fill="#ffffff" opacity="0.14" transform="rotate(-18 320 320)"/><rect x="-120" y="260" width="900" height="58" rx="29" fill="#000000" opacity="0.10" transform="rotate(-18 320 320)"/><rect x="-120" y="400" width="900" height="58" rx="29" fill="#ffffff" opacity="0.10" transform="rotate(-18 320 320)"/>',
    'basketball': '<circle cx="470" cy="170" r="150" fill="#ffffff" opacity="0.14"/><circle cx="470" cy="170" r="150" fill="none" stroke="#000000" stroke-opacity="0.12" stroke-width="10"/><path d="M320 170 h300 M470 20 v300 M350 60 q120 110 240 0 M350 280 q120 -110 240 0" stroke="#000000" stroke-opacity="0.12" stroke-width="10" fill="none"/>',
    'sports':   '<circle cx="480" cy="160" r="140" fill="#ffffff" opacity="0.14"/><circle cx="120" cy="520" r="200" fill="#000000" opacity="0.08"/>',
    '2-player': '<circle cx="200" cy="200" r="120" fill="#ffffff" opacity="0.16"/><circle cx="440" cy="440" r="120" fill="#000000" opacity="0.12"/>',
    'puzzle':   ''.join(f'<rect x="{70 + (i % 3) * 175}" y="{70 + (i // 3) * 175}" width="130" height="130" rx="22" fill="{"#ffffff" if i % 2 else "#000000"}" opacity="{0.14 if i % 2 else 0.09}"/>' for i in range(9)),
    'arcade':   '<circle cx="320" cy="320" r="240" fill="none" stroke="#ffffff" stroke-opacity="0.14" stroke-width="34"/><circle cx="320" cy="320" r="150" fill="none" stroke="#000000" stroke-opacity="0.10" stroke-width="34"/>',
    'io':       ''.join(f'<circle cx="{90 + (i * 173) % 470}" cy="{90 + (i * 257) % 470}" r="{14 + (i * 7) % 26}" fill="#ffffff" opacity="{0.10 + (i % 3) * 0.05}"/>' for i in range(10)),
    'classics': ''.join(f'<rect x="{(i % 4) * 160}" y="{(i // 4) * 160}" width="160" height="160" fill="#000000" opacity="0.08"/>' for i in range(16) if (i % 4 + i // 4) % 2 == 0),
}

def make_thumb(g):
    c1, c2 = palette(g['slug'])
    motif = MOTIFS.get(g['cats'][0], MOTIFS['arcade'])
    ini = initials(g['title'])
    size = 250 if len(ini) <= 2 else 150
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<rect width="640" height="640" fill="url(#g)"/>
{motif}
<text x="320" y="320" text-anchor="middle" dominant-baseline="central"
 font-family="Nunito, 'Arial Black', Arial, sans-serif" font-weight="900" font-size="{size}"
 fill="#000000" opacity="0.18" dy="14">{esc(ini)}</text>
<text x="320" y="320" text-anchor="middle" dominant-baseline="central"
 font-family="Nunito, 'Arial Black', Arial, sans-serif" font-weight="900" font-size="{size}"
 fill="#ffffff">{esc(ini)}</text>
</svg>'''
    path = os.path.join(ROOT, 'assets', 'thumbs', g['slug'] + '.svg')
    with open(path, 'w', encoding='utf-8') as f: f.write(svg)

# ============================================================ shared chrome
STAR = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8z"/></svg>'
PLAY_TRI = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'

def head(title, desc, pre, canonical, extra='', og_image=None):
    og = f'<meta property="og:image" content="{SITE_URL}/{og_image}">' if og_image else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE_URL}/{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{og}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/css/style.css">
{extra}
</head>
<body>'''

LOGO_SVG = '<svg viewBox="0 0 24 24" fill="#111503"><path d="M8 5v14l11-7z"/></svg>'

def header(pre, active=''):
    def cls(k): return ' class="active"' if active == k else ''
    drops = ''.join(f'<a href="{cat_url(c, pre)}">{esc(n[:-6] if n.endswith(" Games") else n)}</a>' for c, (n, _) in CATS.items())
    mob_cats = ''.join(f'<a href="{cat_url(c, pre)}">{esc(n)}</a>' for c, (n, _) in CATS.items())
    return f'''<header class="site-header">
<div class="container header-inner">
<a class="logo" href="{pre}"><span class="logo-mark">{LOGO_SVG}</span>Play<em>Orbit</em></a>
<nav class="main-nav">
<div class="nav-drop"><button type="button">Categories <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M6 9l6 6 6-6"/></svg></button>
<div class="nav-drop-menu">{drops}</div></div>
<a href="{pre}hot-games/"{cls('hot')}>Hot</a>
<a href="{pre}new-games/"{cls('new')}>New</a>
</nav>
<form class="header-search" data-search="{pre}" role="search">
<input type="search" placeholder="Search games…" aria-label="Search games">
<button type="submit" aria-label="Search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg></button>
</form>
<button class="menu-toggle" id="menuToggle" aria-label="Menu"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
</div>
</header>
<nav class="mobile-nav" id="mobileNav">
<div class="container">
<form class="mobile-search" data-search="{pre}" role="search">
<input type="search" placeholder="Search games…" aria-label="Search games">
<button type="submit" aria-label="Search"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg></button>
</form>
<a href="{pre}hot-games/">Hot Games</a>
<a href="{pre}new-games/">New Games</a>
<div class="nav-label">Categories</div>
{mob_cats}
</div>
</nav>'''

def footer(pre):
    cat_links = ''.join(f'<a href="{cat_url(c, pre)}">{esc(n)}</a>' for c, (n, _) in CATS.items())
    return f'''<footer class="site-footer">
<div class="container footer-grid">
<div>
<a class="logo" href="{pre}"><span class="logo-mark">{LOGO_SVG}</span>Play<em>Orbit</em></a>
<p class="footer-blurb">{esc(TAGLINE)} New titles added every week.</p>
</div>
<div><h4>Categories</h4>{cat_links}</div>
<div><h4>Discover</h4>
<a href="{pre}hot-games/">Hot Games</a>
<a href="{pre}new-games/">New Games</a>
<a href="{pre}search/">Search</a>
</div>
<div><h4>Company</h4>
<a href="{pre}about/">About Us</a>
<a href="{pre}contact/">Contact Us</a>
<a href="{pre}privacy/">Privacy Policy</a>
<a href="{pre}terms/">Terms of Use</a>
<a href="{pre}dmca/">Copyright / DMCA</a>
</div>
</div>
<div class="footer-word">PLAYORBIT</div>
<div class="container footer-bottom">
<span class="copy">© 2026 {SITE_NAME}. All rights reserved.</span>
<a href="{pre}privacy/">Privacy</a><a href="{pre}terms/">Terms</a><a href="{pre}dmca/">DMCA</a>
</div>
</footer>
<script src="{pre}assets/js/main.js"></script>
</body>
</html>'''

def game_card(g, pre):
    badge = '<span class="badge">Hot</span>' if g['hot'] else ('<span class="badge new">New</span>' if g['new'] else '')
    return f'''<a class="game-card" href="{game_url(g, pre)}" data-plays="{g['plays']}" data-rating="{g['rating']}" data-added="{g['added']}">
<div class="thumb">{badge}<img loading="lazy" src="{thumb_url(g, pre)}" alt="{esc(g['title'])}" width="320" height="320">
<div class="play-hint"><span>{PLAY_TRI}</span></div></div>
<div class="meta"><div class="title">{esc(g['title'])}</div>
<div class="sub"><span class="star">{STAR}{g['rating']:.1f}</span><span>{fmt_plays(g['plays'])} plays</span></div></div></a>'''

def mini_card(g, pre):
    return f'''<a class="mini-game" href="{game_url(g, pre)}">
<div class="thumb"><img loading="lazy" src="{thumb_url(g, pre)}" alt="{esc(g['title'])}" width="96" height="96"></div>
<div class="t">{esc(g['title'])}</div></a>'''

def ad(cls_, size):
    if not CONFIG.get('ads_enabled'):
        return ''
    return f'<div class="ad-slot {cls_}"><span class="ad-label">Advertisement</span><span class="ad-size">{esc(size)}</span></div>'


# ============================================================ pages
def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: f.write(content)

def clean_output():
    os.makedirs(ROOT, exist_ok=True)
    for name in os.listdir(ROOT):
        if name == 'assets':
            continue
        path = os.path.join(ROOT, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def page_home():
    pre = ''
    popular = sorted(G, key=lambda x: -x['plays'])
    featured = (sorted([g for g in G if g['hot']], key=lambda x: -x['plays']) or popular)[:3]
    hero_items = []
    for i, g in enumerate(featured):
        btn = f'<span class="btn btn-primary">{PLAY_TRI} Play Now</span>' if i == 0 else ''
        hero_items.append(f'''<a class="hero-item" href="{game_url(g, pre)}">
<img src="{thumb_url(g, pre)}" alt="{esc(g['title'])}">
<div class="hero-info"><div><h3>{esc(g['title'])}</h3><p>{esc(g['desc'])}</p></div>{btn}</div></a>''')
    hot = sorted([g for g in G if g['hot']], key=lambda x: -x['plays']) or popular
    new = sorted([g for g in G if g['new']], key=lambda x: x['added'], reverse=True) or popular
    rec = popular[:12]
    chips = ''.join(
        f'<a class="chip" href="{cat_url(c, pre)}"><span class="dot" style="background:{CAT_DOT[c]}"></span>{esc(n[:-6])} <small>{sum(1 for g in G if c in g["cats"])}</small></a>'
        for c, (n, _) in CATS.items())
    rec_cards = []
    for i, g in enumerate(rec):
        rec_cards.append(game_card(g, pre))
        if i == 5: rec_cards.append(ad('ad-slot ad-banner', 'Responsive in-feed ad'))
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME,
          "url": SITE_URL + '/',
          "potentialAction": {"@type": "SearchAction",
              "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + "/search/?q={search_term_string}"},
              "query-input": "required name=search_term_string"}}
    html_doc = head(f'{SITE_NAME} — Free Online Games, Play Instantly', TAGLINE, pre, '',
                    extra=f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    html_doc += header(pre, 'home')
    html_doc += f'''<main class="container">
<section class="hero"><div class="hero-grid">{''.join(hero_items)}</div></section>
<section class="section">
<div class="section-head"><h2><span class="tick">▸</span> Hot Games</h2><a class="more" href="{pre}hot-games/">View all →</a></div>
<div class="game-grid">{''.join(game_card(g, pre) for g in hot[:8])}</div>
</section>
{ad('ad-banner', 'Leaderboard 728×90')}
<section class="section">
<div class="section-head"><h2><span class="tick">▸</span> New Games</h2><a class="more" href="{pre}new-games/">View all →</a></div>
<div class="game-grid">{''.join(game_card(g, pre) for g in new[:8])}</div>
</section>
<section class="section">
<div class="section-head"><h2><span class="tick">▸</span> Browse by Category</h2></div>
<div class="chip-row">{chips}</div>
</section>
<section class="section">
<div class="section-head"><h2><span class="tick">▸</span> Recommended for You</h2></div>
<div class="game-grid">{''.join(rec_cards)}</div>
</section>
</main>'''
    html_doc += footer(pre)
    write('index.html', html_doc)

def page_game(g):
    pre = '../'
    title = g.get('seo_title') or f'Play {g["title"]} Online Free — {SITE_NAME}'
    desc = g.get('meta_desc') or (f'{g["desc"][:140]}…' if len(g['desc']) > 140 else g['desc'])
    cat_names = [CATS[c][0] for c in g['cats']]
    prim = g['cats'][0]
    # related: same primary category first, then popular
    same = [x for x in G if x is not g and prim in x['cats']]
    same.sort(key=lambda x: -x['plays'])
    others = sorted([x for x in G if x is not g and prim not in x['cats']], key=lambda x: -x['plays'])
    related = (same + others)
    left_rel = related[:6]
    right_rel = related[6:12]
    more_rel = related[:10]
    faqs = g.get('faqs') or [
        (f'Is {g["title"]} free to play?',
         f'Yes. {g["title"]} is completely free on {SITE_NAME} — it runs in your browser with no downloads, installs or accounts required.'),
        (f'Can I play {g["title"]} on mobile?',
         f'Yes, {g["title"]} works in most mobile browsers. For the best experience rotate your phone to landscape and use the fullscreen button.'),
        (f'Do I need to download anything to play {g["title"]}?',
         f'No download is needed. Press “Play Now” and the game loads right on this page. Your progress stays in this browser.'),
    ]
    faq_html = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faqs)
    controls = ''.join(f'<li><strong>{esc(k)}</strong> — {esc(v)}</li>' for k, v in g['controls'])
    howto = ''.join(f'<li>{esc(s)}</li>' for s in g['howto'])
    tips = ''.join(f'<li>{esc(s)}</li>' for s in g['tips'])
    tags = ''.join(f'<span class="tag">#{esc(t)}</span>' for t in g['tags'])
    cats_links = ' · '.join(f'<a href="{cat_url(c, pre)}" style="color:var(--accent);font-weight:700">{esc(CATS[c][0])}</a>' for c in g['cats'])
    votes = max(60, int(g['plays'] / 900))
    game_ld = {"@context": "https://schema.org", "@type": "VideoGame", "name": g['title'],
        "url": f'{SITE_URL}/{g["slug"]}/', "image": f"{SITE_URL}/assets/thumbs/" + g.get("thumbfile", g["slug"] + ".svg"),
        "description": g['desc'], "genre": cat_names, "gamePlatform": "Web Browser",
        "applicationCategory": "Game", "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}
    if CONFIG.get('include_aggregate_rating_schema'):
        game_ld["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": f'{g["rating"]:.1f}',
                                      "bestRating": "5", "ratingCount": str(votes)}
    ld = [
        game_ld,
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + '/'},
            {"@type": "ListItem", "position": 2, "name": CATS[prim][0], "item": f'{SITE_URL}/games/{prim}/'},
            {"@type": "ListItem", "position": 3, "name": g['title'], "item": f'{SITE_URL}/{g["slug"]}/'}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
    ]
    stars = ''.join(f'<button type="button" aria-label="Rate {i} stars">{STAR}</button>' for i in range(1, 6))
    extra = ''.join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in ld)
    html_doc = head(title, desc, pre, f'{g["slug"]}/', extra=extra, og_image='assets/thumbs/' + g.get('thumbfile', g['slug'] + '.svg'))
    html_doc += header(pre)
    left_side = (f'''<aside class="play-side left theater-hide"><span class="side-title">You may also like</span>
{''.join(mini_card(x, pre) for x in left_rel)}</aside>''' if left_rel else '')
    right_ad = ad('ad-rect', 'Skyscraper 160×600')
    right_side = (f'''<aside class="play-side right theater-hide">{right_ad}
{('<span class="side-title">More games</span>' + ''.join(mini_card(x, pre) for x in right_rel)) if right_rel else ''}</aside>'''
                  if right_ad or right_rel else '')
    layout_class = 'play-layout'
    if not left_side and not right_side:
        layout_class += ' no-sidebars'
    elif not right_side:
        layout_class += ' no-right'
    elif not left_side:
        layout_class += ' no-left'

    html_doc += f'''<main class="container">
{ad('ad-banner', 'Leaderboard 728×90')}
<nav style="font-size:13px;color:var(--muted);margin-bottom:14px" aria-label="Breadcrumb">
<a href="{pre}" style="font-weight:700">Home</a> › <a href="{cat_url(prim, pre)}" style="font-weight:700">{esc(CATS[prim][0])}</a> › <span style="color:var(--text);font-weight:700">{esc(g['title'])}</span>
</nav>
<div class="{layout_class}">
{left_side}
<div class="stage-wrap">
<div class="stage" id="stage" data-src="{esc(g['url'])}" data-title="{esc(g['title'])}">
<div class="stage-cover" id="stageCover" style="background-image:url('{thumb_url(g, pre)}')">
<h2>{esc(g['title'])}</h2>
<button class="btn btn-primary btn-lg" id="playNow">{PLAY_TRI} Play Now</button>
<span style="color:var(--muted);font-size:13px">Loads the game only after you click</span>
</div>
<div class="stage-loading" id="stageLoading"><div class="spin"></div></div>
<div class="stage-error" id="stageError">
<h3>Game didn’t load</h3>
<p>The game host may be busy or blocking embedded play. You can retry, or open the game in a new tab instead.</p>
<div style="display:flex;gap:10px"><button class="btn" id="retryLoad">Retry</button><button class="btn btn-primary" id="openExternal">Open in new tab</button></div>
</div>
</div>
<div class="game-bar">
<h1>{esc(g['title'])}</h1>
<div class="rate-box" id="rateBox" data-slug="{g['slug']}" data-rating="{g['rating']}" data-count="{votes}">
<span class="rate-stars">{stars}</span>
<span class="rate-num" id="rateNum">{g['rating']:.1f}</span>
<span class="rate-count" id="rateCount">{votes:,} votes</span>
</div>
<button class="btn btn-ghost" id="favBtn" data-slug="{g['slug']}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg><span>Save</span></button>
<button class="btn btn-ghost" id="theaterBtn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 15h18"/></svg>Theater</button>
<button class="btn btn-ghost" id="fsBtn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg>Fullscreen</button>
</div>
</div>
{right_side}
</div>
<section class="content-block">
<h2>About {esc(g['title'])}</h2>
<p>{esc(g['desc'])}</p>
<p style="color:var(--muted);font-size:14px">Categories: {cats_links}</p>
<h3>How to Play</h3><ol>{howto}</ol>
<h3>Controls</h3><ul>{controls}</ul>
<h3>Tips &amp; Tricks</h3><ul>{tips}</ul>
<div class="tag-row">{tags}</div>
</section>
{ad('ad-incontent', 'In-content responsive ad')}
<section class="content-block faq">
<h2>{esc(g['title'])} — FAQ</h2>
{faq_html}
</section>
<section class="section">
<div class="section-head"><h2><span class="tick">▸</span> More Games Like This</h2><a class="more" href="{cat_url(prim, pre)}">More {esc(CATS[prim][0])} →</a></div>
<div class="game-grid">{''.join(game_card(x, pre) for x in more_rel)}</div>
</section>
</main>'''
    html_doc += footer(pre)
    write(f'{g["slug"]}/index.html', html_doc)

def sort_bar(count_label=''):
    return f'''<div class="list-toolbar" id="sortBar">
<button class="sort-btn active" data-sort="popular">Most Popular</button>
<button class="sort-btn" data-sort="new">Newest</button>
<button class="sort-btn" data-sort="rating">Top Rated</button>
<span class="result-count" id="gridCount">{count_label}</span>
</div>'''

def page_list(slug, h1, blurb, games, seo, canonical, active=''):
    pre = '../' * (slug.count('/') + 1)
    cards = ''.join(game_card(g, pre) for g in games)
    html_doc = head(f'{h1} — Play Free Online | {SITE_NAME}', blurb[:155], pre, canonical)
    html_doc += header(pre, active)
    html_doc += f'''<main class="container">
<div class="page-head"><h1>{esc(h1)} <span class="tick">.</span></h1><p>{esc(blurb)}</p></div>
{sort_bar()}
<div class="game-grid" id="sortGrid">{cards}</div>
<div class="load-more-wrap" id="loadMoreWrap"><button class="btn btn-ghost btn-lg" id="loadMore">Load more games</button></div>
{ad('ad-banner', 'Leaderboard 728×90')}
<p class="seo-foot">{esc(seo)}</p>
</main>'''
    html_doc += footer(pre)
    write(slug + '/index.html', html_doc)

def page_search():
    pre = '../'
    html_doc = head(f'Search Games | {SITE_NAME}', 'Search hundreds of free online games by title, category or tag.', pre, 'search/')
    html_doc += header(pre)
    html_doc += f'''<main class="container">
<div class="search-hero">
<h1 style="font-size:30px;font-weight:900;margin-bottom:16px">Search <span style="color:var(--accent)">games</span></h1>
<form data-search="{pre}" role="search">
<input id="searchInput" type="search" placeholder="Try “basketball”, “puzzle”, “drift”…" aria-label="Search games">
<button class="btn btn-primary" type="submit">Search</button>
</form>
</div>
<div class="list-toolbar"><span class="result-count" id="searchCount"></span></div>
<div class="empty-state" id="searchEmpty" style="display:none">
<h2 id="searchTitle">Search games</h2>
<p>No matches — try another keyword, or start with a player favorite below.</p>
</div>
<div class="game-grid" id="searchResults" data-json="{pre}games.json"></div>
<div class="section" id="searchPopularWrap">
<div class="section-head"><h2><span class="tick">▸</span> Popular Right Now</h2></div>
<div class="game-grid" id="searchPopular"></div>
</div>
</main>'''
    html_doc += footer(pre)
    write('search/index.html', html_doc)

def page_static(slug, h1, body):
    pre = '../'
    html_doc = head(f'{h1} | {SITE_NAME}', f'{h1} — {SITE_NAME}', pre, slug + '/')
    html_doc += header(pre)
    html_doc += f'<main class="container"><div class="prose"><h1>{esc(h1)}</h1>{body}</div></main>'
    html_doc += footer(pre)
    write(slug + '/index.html', html_doc)


# ============================================================ static content
ABOUT = f'''<p>{SITE_NAME} is a free browser-games portal. We hand-pick lightweight HTML5 games — basketball, sports, racing, puzzles, arcade classics and more — and make each one playable in a single click, with no downloads, no installs and no accounts.</p>
<h2>What we do</h2>
<ul><li>Curate and test every game before it goes live.</li><li>Write original guides, controls and tips for each title.</li><li>Keep the site fast: games only load after you press Play.</li></ul>
<h2>Who we are</h2>
<p>A small team of casual-gaming fans. {SITE_NAME} started in 2026 as a side project and grows one game at a time.</p>'''

CONTACT = f'''<p>Questions, feedback, a game suggestion or a business inquiry? We read everything.</p>
<h2>Email</h2>
<ul><li>General &amp; feedback — <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
<li>Game submissions (developers) — <a href="mailto:{GAMES_EMAIL}">{GAMES_EMAIL}</a></li>
<li>Copyright / DMCA — <a href="mailto:{LEGAL_EMAIL}">{LEGAL_EMAIL}</a> (see our <a href="../dmca/">DMCA page</a>)</li></ul>
<p>We usually reply within 2–3 business days.</p>'''

PRIVACY = f'''<p><em>Last updated: July 2026.</em> This policy explains what {SITE_NAME} collects when you use the site and why.</p>
<h2>What we collect</h2>
<ul><li><strong>Local preferences.</strong> Favorites and ratings are stored in your browser’s localStorage and never leave your device.</li>
<li><strong>Usage analytics.</strong> We may use privacy-friendly analytics (page views, device type, country) to understand which games people enjoy.</li>
<li><strong>Advertising cookies.</strong> Third-party ad partners may set cookies to show relevant ads and measure campaigns. You can disable cookies in your browser settings.</li></ul>
<h2>What we never do</h2>
<ul><li>We don’t require accounts, names or email addresses to play.</li><li>We don’t sell personal data.</li></ul>
<h2>Third-party games</h2>
<p>Games load from third-party hosts inside an iframe. Those hosts may collect their own technical data under their own privacy policies.</p>
<h2>Contact</h2>
<p>Privacy questions: <a href="mailto:{LEGAL_EMAIL}">{LEGAL_EMAIL}</a>.</p>'''

TERMS = f'''<p><em>Last updated: July 2026.</em> By using {SITE_NAME} you agree to these terms.</p>
<h2>Using the site</h2>
<ul><li>{SITE_NAME} provides links to and embedded playback of third-party browser games for personal, non-commercial entertainment.</li>
<li>You agree not to scrape, mirror or resell the site’s content, and not to interfere with the site’s operation.</li></ul>
<h2>Games and intellectual property</h2>
<p>All games remain the property of their respective developers and publishers. Embedding a game does not transfer any rights. Rights holders can request removal at any time (see <a href="../dmca/">DMCA</a>).</p>
<h2>Advertising</h2>
<p>The site is funded by advertising. Ad placements are provided by third-party networks; we are not responsible for the content of third-party ads.</p>
<h2>No warranty</h2>
<p>The site is provided “as is”. We do our best to keep every game working, but availability of third-party content can change without notice.</p>'''

DMCA = f'''<p>{SITE_NAME} respects the intellectual-property rights of game developers and publishers. If you believe content on this site infringes your copyright, we will act promptly.</p>
<h2>Filing a notice</h2>
<p>Email <a href="mailto:{LEGAL_EMAIL}">{LEGAL_EMAIL}</a> with:</p>
<ol><li>Your name, company and contact details.</li><li>The URL of the page on {SITE_NAME} and identification of the copyrighted work.</li><li>A statement of good-faith belief that the use is unauthorized.</li><li>A statement, under penalty of perjury, that the information is accurate and that you are the rights holder or authorized agent.</li><li>Your physical or electronic signature.</li></ol>
<h2>What happens next</h2>
<p>We review valid notices within 48 hours and remove or disable access to the content where required. We may contact the game host or developer to resolve licensing questions.</p>'''

# ============================================================ main
def main():
    clean_output()
    os.makedirs(os.path.join(ROOT, 'assets', 'thumbs'), exist_ok=True)
    for g in G:
        if 'thumbfile' not in g: make_thumb(g)

    favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#b9f226"/><path d="M26 20l18 12-18 12z" fill="#111503"/></svg>'''
    write('assets/favicon.svg', favicon)

    page_home()
    for g in G: page_game(g)

    for c, (name, blurb) in CATS.items():
        games = sorted([g for g in G if c in g['cats']], key=lambda x: -x['plays'])
        seo = (f'Play the best free {name.lower()} on {SITE_NAME}. Every game runs instantly in your browser on desktop, '
               f'tablet and mobile — no downloads, no sign-ups. We add new {name.lower()} every week, so bookmark this page '
               f'and check back for fresh titles.')
        page_list(f'games/{c}', name, blurb, games, seo, f'games/{c}/')

    popular = sorted(G, key=lambda x: -x['plays'])
    hot = sorted([g for g in G if g['hot']], key=lambda x: -x['plays']) or popular
    new = sorted([g for g in G if g['new']], key=lambda x: x['added'], reverse=True) or popular
    page_list('hot-games', 'Hot Games', 'The most played games on the site right now — ranked by real player counts.',
              hot, f'Trending free games on {SITE_NAME}, ranked by what players actually play. Updated daily.', 'hot-games/', 'hot')
    page_list('new-games', 'New Games', 'Fresh releases and recent additions to the library — newest first.',
              new, f'The newest free browser games on {SITE_NAME}. Check back weekly for new releases.', 'new-games/', 'new')

    page_search()
    page_static('about', 'About Us', ABOUT)
    page_static('contact', 'Contact Us', CONTACT)
    page_static('privacy', 'Privacy Policy', PRIVACY)
    page_static('terms', 'Terms of Use', TERMS)
    page_static('dmca', 'Copyright / DMCA', DMCA)

    # games.json (root-relative; search page prefixes its own depth)
    data = [dict(title=g['title'], slug=g['slug'], url=f'{g["slug"]}/',
                 thumb='assets/thumbs/' + g.get('thumbfile', g['slug'] + '.svg'), categories=[CATS[c][0] for c in g['cats']],
                 tags=g['tags'], rating=g['rating'], plays=g['plays'], isHot=g['hot'], isNew=g['new'])
            for g in G]
    write('games.json', json.dumps(data, ensure_ascii=False, indent=1))

    # sitemap + robots
    urls = [''] + [f'{g["slug"]}/' for g in G] + [f'games/{c}/' for c in CATS] + \
           ['hot-games/', 'new-games/', 'search/', 'about/', 'contact/', 'privacy/', 'terms/', 'dmca/']
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pri = '1.0' if u == '' else ('0.8' if not u.startswith('games/') else '0.6')
        sm.append(f'<url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY}</lastmod><priority>{pri}</priority></url>')
    sm.append('</urlset>')
    write('sitemap.xml', '\n'.join(sm))
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n')

    n = sum(len(fs) for _, _, fs in os.walk(ROOT))
    print(f'OK — {len(G)} games, {len(CATS)} categories, {n} files total')

if __name__ == '__main__':
    main()
