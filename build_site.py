# -*- coding: utf-8 -*-
"""SpeedSlope.net static game site generator.

Reads the full game catalog, publishes the configured subset, and emits HTML
pages, thumbnails, games.json, sitemap.xml and robots.txt into ./app.
"""
import json, os, html, hashlib, colorsys, datetime, shutil, re, struct, zlib

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, 'app')
CONFIG_PATH = os.path.join(BASE, 'site_config.json')
DATA_PATH = os.path.join(BASE, 'games_data.json')
CMS_DATA_DIR = os.path.join(BASE, 'cms-data')
CMS_SITE_SLUG = os.environ.get('SPEEDSLOPE_CMS_SITE', 'speedslope-net')

DEFAULT_CONFIG = {
    'site_name': 'SpeedSlope.net',
    'site_url': 'https://speedslope.net',
    'tagline': 'Free online games, no downloads - play instantly in your browser.',
    'launch_mode': 'single',
    'launch_game_slug': '',
    'home_game_slug': '',
    'contact_email': 'hello@speedslope.net',
    'games_email': 'games@speedslope.net',
    'legal_email': 'legal@speedslope.net',
    'ads_enabled': False,
    'adsense_client': '',
    'include_aggregate_rating_schema': False,
    'turnstile_site_key': '',
}

def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_config():
    cms_config_path = os.path.join(CMS_DATA_DIR, 'sites', CMS_SITE_SLUG + '.json')
    config_path = cms_config_path if os.path.exists(cms_config_path) else CONFIG_PATH
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG.copy()
    user_config = read_json(config_path)
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
TURNSTILE_SITE_KEY = CONFIG.get('turnstile_site_key', '')
ADSENSE_CLIENT = str(CONFIG.get('adsense_client', '') or '').strip()
TODAY = datetime.date.today().isoformat()

ALL_CATS = {
    'slope':      ('Slope Games', 'Play slope games online, including fast 3D reflex games like Speed Slope. Roll, dodge, drift and survive through neon tracks, tunnels and obstacle courses.'),
    'reflex':     ('Reflex Games', 'Fast reflex games built around quick reactions, one-tap timing and instant restarts. Dodge, dash and react before the screen catches up with you.'),
    'basketball': ('Basketball Games', 'Dunk, shoot and score in free basketball games, from clean shot practice to chaotic arcade hoops.'),
    'sports':     ('Sports Games', 'Soccer, golf, archery, pool and more — free sports games that play instantly in the browser.'),
    'racing':     ('Racing Games', 'Drift, drive and battle your way to the finish line in free racing and driving games.'),
    'puzzle':     ('Puzzle Games', 'Work through logic, matching, sliding and sorting challenges with quick browser-friendly puzzle games.'),
    'arcade':     ('Arcade Games', 'Fast, addictive arcade games with short loops, clean controls and instant restarts.'),
    '2-player':   ('2 Player Games', 'Grab a friend and share the keyboard for same-screen battles, races and co-op runs.'),
    'io':         ('IO Games', 'Jump into free .io games and compete in territory battles, survival arenas and quick multiplayer rounds.'),
    'classics':   ('Classic Games', 'Timeless browser classics including 2048, Mahjong, Pool and Solitaire.'),
    'runner':     ('Runner Games', 'Keep moving in endless runner games built around timing, rhythm and quick reactions.'),
    'driving':    ('Driving Games', 'Take the wheel in free driving games that reward control, lane reading and steady hands.'),
    'stunt':      ('Stunt Games', 'Launch, flip and land cleanly in stunt-heavy games with speed and momentum.'),
    'motorcycle': ('Motorcycle Games', 'Ride bikes and motorbikes through speed runs, stunt tracks and rough terrain.'),
    'car-racing': ('Car Racing Games', 'High-speed car games built around track control, traffic reading and sharp cornering.'),
    'obstacle-course': ('Obstacle Course Games', 'Thread the needle through platform traps, gaps and hazards in obstacle-course games.'),
    'platformer': ('Platformer Games', 'Jump, climb and time your way through free browser platformers and traversal games.'),
    'football':   ('Football Games', 'Free football games with penalties, arcade headers and quick goal-scoring action.'),
    'soccer':     ('Soccer Games', 'Kick, flick and shoot in soccer games built for quick browser play.'),
    'archery':    ('Archery Games', 'Aim carefully and release clean shots in free archery games.'),
    'pool':       ('Pool Games', 'Line up angles and sink balls in free pool and billiards games.'),
    'golf':       ('Golf Games', 'Putt, aim and steer the ball through compact golf challenges.'),
    'shooting':   ('Shooting Games', 'Aim-based games where timing, targeting and precision matter more than brute force.'),
    'strategy':   ('Strategy Games', 'Think ahead in lane-control, territory and tactical browser games.'),
    'card':       ('Card Games', 'Classic card games, from solitaire variants to relaxed browser decks.'),
    'solitaire':  ('Solitaire Games', 'Free solitaire games with quick setups and calm solo play.'),
    'mahjong':    ('Mahjong Games', 'Tile-matching mahjong games with fast resets and clean board reads.'),
    'word':       ('Word Games', 'Word search and language games for quick, low-pressure play.'),
    'sorting':    ('Sorting Games', 'Arrange, classify and untangle objects in tidy sorting games.'),
    'merge':      ('Merge Games', 'Combine matching pieces and climb numbers in merge games.'),
    'fighting':   ('Fighting Games', 'Face off in duels, brawls and combat-focused browser games.'),
}

CAT_DOT = {
    'slope': '#b9f226',
    'reflex': '#ff7a45',
    'basketball': '#ff9f43', 'sports': '#3ddc84', 'racing': '#ff5d5d', 'puzzle': '#b98cff',
    'arcade': '#4dc3ff', '2-player': '#ffd93d', 'io': '#ff6ec7', 'classics': '#9aa78b',
}

def cat_color(key):
    if key in CAT_DOT:
        return CAT_DOT[key]
    h = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
    hue = h % 360
    sat = 62 + (h >> 8) % 16
    light = 52 + (h >> 16) % 10
    r, g, b = colorsys.hls_to_rgb(hue / 360, light / 100, sat / 100)
    return '#%02x%02x%02x' % tuple(round(x * 255) for x in (r, g, b))

REMOVED_GAME_SLUGS = {
    '2-player-dark-racing', '2-player-moto-racing', '2048-merge-world',
    '2048-snake-io', 'ace-car-racing', 'animal-klotski',
    'archer-vs-monsters', 'archery-legends', 'archery-master-bow-and-arrow',
    'basketball-fever', 'basketball-life-3d', 'basketball-rush',
    'basketball-stars-2026', 'billiard-diamond-challenge', 'bloons-survival-io',
    'bounce-dunk-basketball', 'city-drift-racing', 'colorwars-io-conquest-game',
    'drift-car-driving',
    'crazy-bike-stunts-pvp', 'fireboy-watergirl-7-and-friends',
    'flick-shot-soccer', 'football-heads-2026', 'football-penalty-2026',
    'formula-car-circuit-racing', 'formula-racing-games-car-game', 'fun-golf',
    'golf-mini', 'golf-orbit', 'mahjong-duels', 'mahjong-match-line',
    'mahjong-tile-club', 'marble-sort', 'martial-arts-fighter-duel',
    'merge-blocks-2048', 'mini-golf-battle', 'mini-golf-saga', 'money-2048',
    'moto-race-city', 'moto-trials-rush', 'mystic-word-quests',
    'nsr-street-car-racing', 'office-spider-solitaire', 'on-fire-basketball-shots',
    'paperwar-io', 'pixel-mini-golf', 'pool-8', 'pool-duel', 'pool-master',
    'prismroll-3d', 'push-io', 'race-it-car-racing', 'racing-game-king-hp',
    'robin-hood-archer', 'shanghai-town', 'slippery-drift-racing', 'slithoria',
    'snake-duel', 'snakelands-io', 'solitaire-klondike-eternal-russian-classic',
    'solitaire-quest', 'stickman-temple-duel', 'tank-duel-3d', 'tetro-merge',
    'the-drag-racing-challenge', 'theme-word-search', 'tiny-golf-king',
    'traffic-racing', 'triple-shelf-match', 'word-search-universe-2',
    'word-search-universe-animals', 'world-cup-2026-soccer-game', 'zen-solitaire',
}


def select_games(all_games):
    all_games = [g for g in all_games if g['slug'] not in REMOVED_GAME_SLUGS]
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

def normalize_pairs(items, first, second):
    result = []
    for item in items or []:
        if isinstance(item, dict):
            result.append([item.get(first, ''), item.get(second, '')])
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            result.append([item[0], item[1]])
    return result


def normalize_game(game):
    game = dict(game)
    game['controls'] = normalize_pairs(game.get('controls'), 'key', 'action')
    if 'faqs' in game:
        game['faqs'] = normalize_pairs(game.get('faqs'), 'question', 'answer')
    return game


def load_games_data():
    cms_games_dir = os.path.join(CMS_DATA_DIR, 'games')
    if os.path.isdir(cms_games_dir):
        games = [
            normalize_game(read_json(os.path.join(cms_games_dir, name)))
            for name in os.listdir(cms_games_dir)
            if name.endswith('.json')
        ]
        return sorted(games, key=lambda g: (g.get('sort_order', 999999), g['slug']))
    return [normalize_game(g) for g in read_json(DATA_PATH)]


# slug, title, iframe URL, categories[0]=primary, tags, rating, plays, hot, new,
# added, description, howto[], controls[(key, action)], tips[]
ALL_GAMES = load_games_data()
G = select_games(ALL_GAMES)
def enrich_categories(game):
    cats = list(dict.fromkeys(game['cats']))
    text = ' '.join([game['slug'], game['title'], ' '.join(game.get('tags', []))]).lower()

    def add(*keys):
        for key in keys:
            if key in ALL_CATS and key not in cats:
                cats.append(key)

    if game['slug'] == 'speed-slope':
        add('runner', 'car-racing', 'obstacle-course', 'arcade')
    if game['slug'] == 'highway-driver-3d':
        add('driving', 'car-racing')
    if game['slug'] == 'formula-car-circuit-racing':
        add('driving', 'car-racing')
    if game['slug'] == 'bike-racing-adventure':
        add('motorcycle', 'stunt', 'car-racing')
    if game['slug'] == 'apex-racer':
        add('driving', 'car-racing')
    if game['slug'] == 'prismroll-3d':
        add('obstacle-course', 'sorting', 'puzzle')
    if game['slug'] == 'obby-three-challenges':
        add('obstacle-course', 'platformer', 'runner')
    if game['slug'] == 'nullpulse-runner':
        add('runner', 'platformer', 'arcade')
    if game['slug'] == 'mario-jetpack-rush':
        add('runner', 'platformer', 'arcade')
    if game['slug'] == 'hop-hop':
        add('runner', 'platformer', 'arcade')
    if game['slug'] == 'fireboy-watergirl-7-and-friends':
        add('2-player', 'platformer', 'obstacle-course', 'puzzle')
    # Their titles would otherwise auto-create one-game football, soccer and
    # merge category pages; the two-player and classic puzzle homes are better.
    if game['slug'] in {'soccer-random', '2048-x2-legends'}:
        return cats

    if 'basketball' in text:
        add('basketball', 'sports', 'shooting', 'arcade')
    if any(term in text for term in ('football', 'soccer')):
        add('football', 'soccer', 'sports', 'shooting')
    if 'golf' in text:
        add('golf', 'sports')
    if 'archery' in text:
        add('archery', 'sports', 'shooting')
    if 'pool' in text:
        add('pool', 'sports', 'strategy')

    if any(term in text for term in ('racing', 'race', 'racer', 'driver', 'driving')):
        add('racing', 'driving')
    if any(re.search(rf'(?<![a-z0-9]){term}(?![a-z0-9])', text) for term in ('car', 'formula', 'highway', 'apex')):
        add('car-racing')
    if any(term in text for term in ('moto', 'motor', 'bike')):
        add('motorcycle', 'stunt', 'car-racing')

    if any(term in text for term in ('runner', 'jetpack', 'hop hop')):
        add('runner', 'platformer', 'arcade')
    if any(term in text for term in ('obby', 'fireboy', 'watergirl', 'prismroll')):
        add('obstacle-course', 'platformer')
    if 'duel' in text or '2 player' in text:
        add('2-player')
        if 'duel' in text and not any(term in text for term in ('pool', 'solitaire')):
            add('fighting')

    if re.search(r'(?<![a-z0-9])(?:io|\.io)(?![a-z0-9])', text):
        add('io')
    if any(term in text for term in ('snake', 'paperwar', 'colorwars', 'push', 'bloons')):
        add('io', 'strategy')

    if 'solitaire' in text:
        add('card', 'solitaire', 'classics')
    if 'mahjong' in text:
        add('mahjong', 'classics', 'puzzle')
    if 'chess' in text:
        add('strategy', 'classics')
    if 'word' in text:
        add('word', 'puzzle')
    if any(term in text for term in ('marble', 'sort', 'klotski', 'shelf match')):
        add('sorting', 'puzzle')
    if any(term in text for term in ('2048', 'merge')):
        add('merge', 'classics')
    if 'tank' in text:
        add('fighting', 'shooting', 'strategy', '2-player')
    if 'bloons' in text:
        add('shooting', 'strategy')
    if 'push.io' in text or game['slug'] == 'push-io':
        add('arcade')
    return cats

for g in G:
    g['cats'] = enrich_categories(g)
ACTIVE_CAT_KEYS = {c for g in G for c in g['cats']}
CATS = {k: v for k, v in ALL_CATS.items() if k in ACTIVE_CAT_KEYS}

# ============================================================ helpers
def esc(s): return html.escape(str(s), quote=True)

def fmt_plays(n):
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000: return f'{n/1_000:.1f}'.rstrip('0').rstrip('.') + 'K'
    return str(n)

BY_SLUG = {g['slug']: g for g in G}

FEATURED_CATEGORY_GAMES = {
    'slope': 'speed-slope',
    'reflex': 'crazy-neon-square-rush',
    'basketball': 'bounce-dunk-basketball',
    'sports': 'neon-mini-golf',
    'racing': 'speed-slope',
    'puzzle': 'marble-sort',
    'arcade': 'nullpulse-runner',
    '2-player': 'boxing-random',
    'classics': 'chess-3d',
    'runner': 'nullpulse-runner',
    'driving': 'highway-driver-3d',
    'stunt': 'bike-racing-adventure',
    'motorcycle': 'bike-racing-adventure',
    'car-racing': 'car-drive-simulator',
    'obstacle-course': 'obby-three-challenges',
    'platformer': 'fireboy-watergirl-7-and-friends',
    'football': 'world-cup-2026-soccer-game',
    'soccer': 'world-cup-2026-soccer-game',
    'archery': 'archery-legends',
    'pool': 'pool-duel',
    'golf': 'neon-mini-golf',
    'shooting': 'bubble-shooter-free-3',
    'strategy': 'chess-3d',
    'word': 'word-search-universe-animals',
    'sorting': 'stack-sorting',
    'fighting': 'martial-arts-fighter-duel',
}

REMOVED_CATEGORY_REDIRECTS = {
    '2-player': 'arcade',
    'archery': 'arcade',
    'basketball': 'arcade',
    'card': 'classics',
    'fighting': 'arcade',
    'football': 'arcade',
    'golf': 'arcade',
    'io': 'arcade',
    'mahjong': 'classics',
    'merge': 'puzzle',
    'pool': 'classics',
    'shooting': 'arcade',
    'soccer': 'arcade',
    'solitaire': 'classics',
    'sorting': 'puzzle',
    'sports': 'arcade',
    'word': 'puzzle',
}

SLOPE_GAME_ANGLES = {
    'nullpulse-runner': 'Nullpulse Runner is one of the closest games like Speed Slope in this collection: it keeps the neon look, quick restarts, and reflex-first rhythm, but changes the challenge from steering a rolling ball to timing jumps through a glowing runner course.',
    'obby-three-challenges': 'Obby: Three Challenges fits Speed Slope players who enjoy obstacle timing and instant failure loops. The movement is more platformer-like, but the appeal is similar: learn the pattern, stay calm, and try one cleaner run.',
    'extreme-ball-balancer-3d': 'Extreme Ball Balancer 3D slows the rolling-ball idea down and turns precision into the challenge. There is no downhill rush here — just narrow rails, shifting traps and a ball that punishes any correction you rush.',
    'stack-ball-run-3d': 'Stack Ball Run 3D is the greediest game in this collection. You are still running a ball down a track, but every ball you collect makes you bigger and harder to steer, so the run becomes a negotiation between score and survival.',
    'running-roadball': 'Running Roadball is the closest thing here to a rhythm game. The neon tracks follow the music, so clean runs come from tapping on the beat rather than reacting to obstacles that have already arrived.',
    'endless-tunnel-run': 'Endless Tunnel Run strips the slope down to a tunnel and keeps accelerating. If you like Speed Slope for the way the speed quietly climbs while you are concentrating, this delivers the same pressure with walls instead of open edges.',
    'rainbow-color-ball-runner': 'Rainbow Color Ball Runner keeps the rolling ball and adds a colour rule on top. The steering feels familiar, but now the balls you collect have to match, which turns every straight into a small decision.',
    'big-rolling-ball': 'Big Rolling Ball is the simplest rolling-ball game on the site — one path, one ball, obstacles arriving faster than you would like. It makes a good warm-up before a Speed Slope session.',
    'momentum': 'Momentum borrows the three-lane running of an endless runner and adds worlds that change as you speed up. The lane discipline you learn here translates directly back to staying centred on a fast slope.',
    'spherix': "Spherix is the thinking player's rolling-ball game. Instead of reacting to what is coming, you plan a route through 25 mazes — the same ball control, a completely different kind of pressure.",
    'zigzag-puzzle': 'ZigZag Puzzle is the smallest idea in the collection: one ball, one wall, one tap that reverses direction. It is the purest test of the same tap-timing that keeps you on a slope.',
    'twist-and-roll': 'Twist and Roll turns ball control into a physics puzzle by letting you rotate the level itself. If you like the weight and momentum of the Speed Slope ball, this is that feeling slowed down and made deliberate.',
    'snow-ball-race': 'Snow Ball Race swaps the neon slope for a snowy track but keeps the growing-ball problem: collect snow and you get bigger, and bigger means harder to steer through the obstacles ahead.',
    'snow-slider-3d': 'Snow Slider 3D is the downhill counterpart in this collection. Trees, rocks and snowmen take the place of blocks and gaps, and the speed climbs the further down the mountain you get.',
    'gliding-over-dunes': 'Gliding over Dunes is a one-touch distance game rather than a dodging game, but the timing instinct is the same. Build speed, release at the right moment and read the landing before you commit.',
    'snowboard-game': 'Snowboard Game is the most traditional downhill run here: icy slopes, barriers and obstacles, and a clean line to find. It is a good pick if you want the slope feel with a board instead of a ball.',
    'crazy-neon-square-rush': 'Crazy Neon Square Rush is the flat, top-down version of the Speed Slope idea. The square scrolls upward on its own, your score climbs while you survive, and the only control is which side you slide to.',
    'velocity-breaker': 'Velocity Breaker adds a dash to the neon tunnel formula. It is the most aggressive game in this collection, and the dash works exactly like a slope correction that you have to make a fraction of a second early.',
    'orbit-rush-3d': 'Orbit Rush 3D puts you inside the ball while the tunnel rotates around you. The ring gaps demand the same early line-up as a slope lane change, and the power-ups change how the next stretch should be played.',
}

def home_game():
    slug = CONFIG.get('home_game_slug') or CONFIG.get('launch_game_slug') or G[0]['slug']
    game = BY_SLUG.get(slug)
    if not game:
        raise ValueError(f'home_game_slug not selected for publishing: {slug}')
    return game

def game_url(g, pre):
    if g['slug'] == home_game()['slug']:
        return pre
    return f'{pre}{g["slug"]}/'
def cat_url(c, pre): return f'{pre}games/{c}/'
def thumb_file(g): return g.get('thumbfile', g['slug'] + '.png')
def thumb_url(g, pre): return f"{pre}assets/thumbs/{thumb_file(g)}"
def thumb_abs_url(g): return f"{SITE_URL}/assets/thumbs/{thumb_file(g)}"

def game_abs_url(g):
    return SITE_URL + '/' if g['slug'] == home_game()['slug'] else f'{SITE_URL}/{g["slug"]}/'

def page_abs_url(g, canonical):
    if canonical == '':
        return SITE_URL + '/'
    return game_abs_url(g)

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

def write_png(path, w, h, rgb_at):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(rgb_at(x, y))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def make_speed_slope_png(path, size=640):
    def rgb_at(x, y):
        t = y / (size - 1)
        r = int(3 + 4 * (1 - t))
        g = int(10 + 32 * (1 - t))
        b = int(8 + 22 * (1 - t))
        cx = size / 2
        if y > size * 0.18:
            road_w = 34 + (y - size * 0.18) / (size * 0.82) * (size * 0.92)
            left, right = cx - road_w / 2, cx + road_w / 2
            if left < x < right:
                r, g, b = 4, 28, 20
                if min(abs(x - left), abs(x - right)) < 4:
                    r, g, b = 90, 255, 60
                lane = abs(((x - cx) / max(road_w, 1) * 8) % 1 - .5)
                if lane < .035:
                    r, g, b = max(r, 30), max(g, 170), max(b, 45)
                grid = (y - size * 0.18) / (size * 0.82)
                if abs((grid * grid * 18) % 1) < .035:
                    r, g, b = max(r, 50), max(g, 220), max(b, 70)
        dx, dy = x - cx, y - size * 0.46
        d = (dx * dx + dy * dy) ** .5
        if 34 < d < 48:
            r, g, b = 110, 255, 65
        elif d <= 34:
            r, g, b = 3, 18, 14
        return r, g, b
    write_png(path, size, size, rgb_at)


def make_icon_png(path, size):
    def rgb_at(x, y):
        cx = cy = size / 2
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** .5
        if r > size * .46:
            return 0, 0, 0
        if x > size * .39 and x < size * .39 + (y - size * .30) * .85 and x < size * .39 + (size * .70 - y) * .85 and size * .30 < y < size * .70:
            return 17, 21, 3
        return 185, 242, 38
    write_png(path, size, size, rgb_at)


def make_thumb(g):
    if g['slug'] == 'speed-slope':
        make_speed_slope_png(os.path.join(ROOT, 'assets', 'thumbs', 'speed-slope.png'))
        return
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
def _asset_version(rel):
    # Content-hash the asset so returning visitors never run stale cached
    # CSS/JS against new markup.
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return '1'
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:8]

CSS_V = _asset_version('assets/css/style.css')
JS_V = _asset_version('assets/js/main.js')

STAR = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8z"/></svg>'
PLAY_TRI = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'

def adsense_snippet():
    """Google AdSense site-ownership snippet.

    AdSense verifies ownership by finding this loader in the <head> of the
    pages it crawls, so it is emitted whenever an adsense_client is
    configured. It is deliberately independent of ads_enabled: verification
    must work before any ad slot is switched on.
    """
    if not ADSENSE_CLIENT:
        return ''
    return (
        f'<meta name="google-adsense-account" content="{ADSENSE_CLIENT}">\n'
        f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>'
    )


def head(title, desc, pre, canonical, extra='', og_image=None, ads=True):
    social_image = f'{SITE_URL}/{og_image}' if og_image else ''
    adsense = adsense_snippet() if ads else ''
    adsense_block = f'{adsense}\n' if adsense else ''
    og = f'<meta property="og:image" content="{social_image}">\n<meta property="og:image:width" content="640">\n<meta property="og:image:height" content="640">' if og_image else ''
    twitter_image = f'<meta name="twitter:image" content="{social_image}">' if og_image else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{adsense_block}<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{SITE_URL}/{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{og}
<meta name="twitter:card" content="summary_large_image">
{twitter_image}
<link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{pre}assets/favicon-48x48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="{pre}assets/apple-touch-icon.png">
<link rel="manifest" href="{pre}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/css/style.css?v={CSS_V}">
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
<a class="logo" href="{pre}"><span class="logo-mark">{LOGO_SVG}</span>Speed<em>Slope</em></a>
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
    turnstile = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>' if TURNSTILE_SITE_KEY else ''
    return f'''<footer class="site-footer">
<div class="container footer-grid">
<div>
<a class="logo" href="{pre}"><span class="logo-mark">{LOGO_SVG}</span>Speed<em>Slope</em></a>
<p class="footer-blurb">{esc(TAGLINE)} New titles added every week.</p>
</div>
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
<div class="footer-word">SPEED SLOPE</div>
<div class="container footer-bottom">
<span class="copy">© 2026 {SITE_NAME}. All rights reserved.</span>
<a href="{pre}privacy/">Privacy</a><a href="{pre}terms/">Terms</a><a href="{pre}dmca/">DMCA</a>
</div>
</footer>
{turnstile}
<script src="{pre}assets/js/main.js?v={JS_V}"></script>
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
    return f'''<a class="mini-game" href="{game_url(g, pre)}" aria-label="Play {esc(g['title'])}">
<div class="thumb"><img loading="lazy" src="{thumb_url(g, pre)}" alt="" width="96" height="96"></div></a>'''

def ad(cls_, size):
    if not CONFIG.get('ads_enabled'):
        return ''
    return f'<div class="ad-slot {cls_}"><span class="ad-label">Advertisement</span><span class="ad-size">{esc(size)}</span></div>'


def comments_section(g, pre):
    sitekey = esc(TURNSTILE_SITE_KEY)
    turnstile = f'<div class="cf-turnstile" data-sitekey="{sitekey}"></div>' if sitekey else '<p class="comment-note">Comment posting is waiting for spam-check setup.</p>'
    disabled = '' if sitekey else ' disabled'
    return f'''<section class="content-block comments-panel" id="comments" data-comments data-slug="{esc(g['slug'])}">
<div class="comments-head"><div><h2>Comments</h2><p>Share a quick note about this game. Email is optional and never shown publicly.</p></div><span id="commentsCount">0 comments</span></div>
<div class="comments-list" id="commentsList"><p class="comment-note">Loading comments...</p></div>
<form class="comment-form" id="commentForm">
<div class="comment-fields"><label>Name <input name="displayName" maxlength="60" autocomplete="name" placeholder="Anonymous"></label><label>Email <input name="email" maxlength="254" autocomplete="email" inputmode="email" placeholder="Optional"></label></div>
<label>Comment <textarea name="body" maxlength="1000" required placeholder="What did you think?"></textarea></label>
<label class="comment-hp">Website <input name="website" tabindex="-1" autocomplete="off"></label>
{turnstile}
<div class="comment-actions"><button class="btn btn-primary" type="submit"{disabled}>Post comment</button><span id="commentStatus" class="comment-note"></span></div>
</form>
</section>'''


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
    if CONFIG.get('launch_mode', 'single') == 'single':
        # Single-game site: the home page IS the play page — the game loads
        # automatically, no extra click. The /slug/ URL redirects here.
        write('index.html', game_page_html(home_game(), pre='', canonical='', autoplay=True, breadcrumb=False))
        return
    if CONFIG.get('home_game_slug') or CONFIG.get('launch_game_slug'):
        # Curated vertical site: keep the home page focused on the flagship
        # game, while related selected games appear in the sidebars and lists.
        write('index.html', game_page_html(home_game(), pre='', canonical='', autoplay=True, breadcrumb=False))
        return
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
        f'<a class="chip" href="{cat_url(c, pre)}"><span class="dot" style="background:{cat_color(c)}"></span>{esc(n[:-6])} <small>{sum(1 for g in G if c in g["cats"])}</small></a>'
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

def game_page_html(g, pre='../', canonical=None, autoplay=False, breadcrumb=True):
    if canonical is None:
        canonical = f'{g["slug"]}/'
    title = g.get('seo_title') or f'Play {g["title"]} Online Free — {SITE_NAME}'
    desc = g.get('meta_desc') or (f'{g["desc"][:140]}…' if len(g['desc']) > 140 else g['desc'])
    cat_names = [CATS[c][0] for c in g['cats']]
    prim = g['cats'][0]
    # related: same primary category first, then popular
    same = [x for x in G if x is not g and prim in x['cats']]
    same.sort(key=lambda x: -x['plays'])
    others = sorted([x for x in G if x is not g and prim not in x['cats']], key=lambda x: -x['plays'])
    related = (same + others)
    left_rel = related[:7]
    right_rel = related[7:14]
    more_rel = related[:10]
    faqs = g.get('faqs') or [
        (f'Is {g["title"]} free to play?',
         f'Yes. {g["title"]} is completely free on {SITE_NAME} — it runs in your browser with no downloads, installs or accounts required.'),
        (f'Can I play {g["title"]} on mobile?',
         f'Yes, {g["title"]} works in most mobile browsers. For the best experience rotate your phone to landscape and use the fullscreen button.'),
        (f'Do I need to download anything to play {g["title"]}?',
         f'No download is needed. The game loads automatically right on this page. Your progress stays in this browser.'),
    ]
    faq_html = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faqs)
    controls = ''.join(f'<li><strong>{esc(k)}</strong> — {esc(v)}</li>' for k, v in g['controls'])
    howto = ''.join(f'<li>{esc(s)}</li>' for s in g['howto'])
    tips = ''.join(f'<li>{esc(s)}</li>' for s in g['tips'])
    tags = ''.join(f'<span class="tag">#{esc(t)}</span>' for t in g['tags'])
    cats_links = ' · '.join(f'<a href="{cat_url(c, pre)}" style="color:var(--accent);font-weight:700">{esc(CATS[c][0])}</a>' for c in g['cats'])
    slope_angle = ''
    if 'slope' in g['cats'] and g['slug'] != home_game()['slug']:
        slope_angle_text = SLOPE_GAME_ANGLES.get(
            g['slug'],
            f'{g["title"]} belongs in Slope Games because it gives Speed Slope players another quick browser game built around speed, timing, and repeatable skill.'
        )
        slope_angle = f'<h3>Why Speed Slope Fans Might Like It</h3><p>{esc(slope_angle_text)}</p>'
    votes = max(60, int(g['plays'] / 900))
    game_ld = {"@context": "https://schema.org", "@type": "VideoGame", "name": g['title'],
        "url": page_abs_url(g, canonical), "image": thumb_abs_url(g),
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
            {"@type": "ListItem", "position": 3, "name": g['title'], "item": page_abs_url(g, canonical)}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
    ]
    stars = ''.join(f'<button type="button" aria-label="Rate {i} stars">{STAR}</button>' for i in range(1, 6))
    extra = ''.join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in ld)
    html_doc = head(title, desc, pre, canonical, extra=extra, og_image='assets/thumbs/' + thumb_file(g))
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

    crumb = ''
    if breadcrumb:
        crumb = f'''<nav style="font-size:13px;color:var(--muted);margin-bottom:14px" aria-label="Breadcrumb">
<a href="{pre}" style="font-weight:700">Home</a> › <a href="{cat_url(prim, pre)}" style="font-weight:700">{esc(CATS[prim][0])}</a> › <span style="color:var(--text);font-weight:700">{esc(g['title'])}</span>
</nav>'''
    autoplay_attr = ' data-autoplay="1"' if autoplay else ''
    error_box = '''<div class="stage-error" id="stageError">
<h3>Game didn’t load</h3>
<p>The game host may be busy or blocking embedded play. You can retry, or open the game in a new tab instead.</p>
<div style="display:flex;gap:10px"><button class="btn" id="retryLoad">Retry</button><button class="btn btn-primary" id="openExternal">Open in new tab</button></div>
</div>'''
    if autoplay:
        # No click gate: the iframe is rendered right into the HTML so the
        # game starts loading with the page itself, even before/without JS.
        stage_inner = f'''<div class="stage-loading show" id="stageLoading"><img class="stage-preview-img" src="{thumb_url(g, pre)}" alt="{esc(g['title'])} online game screenshot" width="640" height="640"><div class="spin"></div></div>
<iframe id="gameFrame" src="{esc(g['url'])}" title="{esc(g['title'])}" allow="autoplay; fullscreen; gamepad; keyboard-map; xr-spatial-tracking; cross-origin-isolated" allowfullscreen></iframe>
{error_box}'''
    else:
        stage_inner = f'''<div class="stage-cover" id="stageCover" style="background-image:url('{thumb_url(g, pre)}')">
<img class="stage-preview-img" src="{thumb_url(g, pre)}" alt="{esc(g['title'])} online game screenshot" width="640" height="640">
<h2>{esc(g['title'])}</h2>
<button class="btn btn-primary btn-lg" id="playNow">{PLAY_TRI} Play Now</button>
<span style="color:var(--muted);font-size:13px">Loads the game only after you click</span>
</div>
<div class="stage-loading" id="stageLoading"><div class="spin"></div></div>
{error_box}'''
    more_section = ''
    if more_rel:
        more_section = f'''<section class="section">
<div class="section-head"><h2><span class="tick">▸</span> More Games Like This</h2><a class="more" href="{cat_url(prim, pre)}">More {esc(CATS[prim][0])} →</a></div>
<div class="game-grid">{''.join(game_card(x, pre) for x in more_rel)}</div>
</section>'''

    html_doc += f'''<main class="container">
{ad('ad-banner', 'Leaderboard 728×90')}
{crumb}
<div class="{layout_class}">
{left_side}
<div class="stage-wrap">
<div class="stage" id="stage" data-src="{esc(g['url'])}" data-title="{esc(g['title'])}"{autoplay_attr}>
{stage_inner}
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
<button class="btn btn-ghost" id="shareBtn" data-title="{esc(g['title'])}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M12 3v12M8 7l4-4 4 4M5 14v5a2 2 0 002 2h10a2 2 0 002-2v-5"/></svg><span>Share</span></button>
<button class="btn btn-ghost" id="reportBtn" aria-haspopup="dialog"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M5 21V4m0 1h12l-2 4 2 4H5"/></svg><span>Report</span></button>
</div>
</div>
<dialog id="reportModal" class="report-modal" aria-labelledby="reportTitle">
<form id="reportForm" data-report-api="/api/reports" data-slug="{g['slug']}">
<h3 id="reportTitle">Report {esc(g['title'])}</h3>
<label>What happened?
<select name="issue" required>
<option value="">Choose a reason</option>
<option value="not-loading">Game did not load</option>
<option value="not-working">Game is not working</option>
<option value="progress">Lost progress</option>
<option value="inappropriate">Inappropriate content</option>
<option value="purchase">In-game purchase issue</option>
<option value="other">Other issue</option>
</select>
</label>
<label>Details (optional)
<textarea name="details" maxlength="500" placeholder="Tell us what you saw. Do not include links."></textarea>
</label>
<label class="comment-hp">Website <input name="website" tabindex="-1" autocomplete="off"></label>
<div class="report-actions">
<button class="btn btn-ghost" type="button" data-close-report>Cancel</button>
<button class="btn btn-primary" type="submit">Send report</button>
</div>
<p class="comment-note" id="reportStatus" role="status"></p>
</form>
</dialog>
{right_side}
</div>
{comments_section(g, pre)}
<section class="content-block">
<h2>About {esc(g['title'])}</h2>
<p>{esc(g['desc'])}</p>
{slope_angle}
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
{more_section}
</main>'''
    html_doc += footer(pre)
    return html_doc

def page_redirect(rel, target, label):
    adsense = adsense_snippet()
    adsense_block = f'{adsense}\n' if adsense else ''
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{adsense_block}<title>{esc(label)} | {SITE_NAME}</title>
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{SITE_URL}/{target}">
<meta http-equiv="refresh" content="0; url={SITE_URL}/{target}">
</head>
<body>
<p>This page has moved to <a href="{SITE_URL}/{target}">{SITE_URL}/{target}</a>.</p>
<script>location.replace({json.dumps(SITE_URL + '/' + target)});</script>
</body>
</html>'''
    write(rel, html_doc)

def page_game(g):
    if g['slug'] == home_game()['slug']:
        # Single-game site: home is the play page, so the /slug/ URL just
        # redirects there (avoids duplicate content).
        page_redirect(f'{g["slug"]}/index.html', '', f'Play {g["title"]} Online Free')
        return
    write(f'{g["slug"]}/index.html', game_page_html(g))

def sort_bar(count_label=''):
    return f'''<div class="list-toolbar" id="sortBar">
<button class="sort-btn active" data-sort="popular">Most Popular</button>
<button class="sort-btn" data-sort="new">Newest</button>
<button class="sort-btn" data-sort="rating">Top Rated</button>
<span class="result-count" id="gridCount">{count_label}</span>
</div>'''

def item_list_ld(name, canonical, games):
    return {"@context": "https://schema.org", "@type": "ItemList", "name": name,
            "url": f'{SITE_URL}/{canonical}', "numberOfItems": len(games),
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": game_abs_url(g), "name": g['title'], "image": thumb_abs_url(g)}
                for i, g in enumerate(games[:24])
            ]}


def category_player(canonical, pre, games):
    cat = canonical.removeprefix('games/').strip('/')
    featured_slug = FEATURED_CATEGORY_GAMES.get(cat, '')
    g = next((x for x in games if x['slug'] == featured_slug), games[0] if games else None)
    if not g:
        return ''
    alts = [x for x in games if x['slug'] != g['slug']][:3]
    alt_links = ''.join(f'''<a class="category-alt-game" href="{game_url(x, pre)}" aria-label="Play {esc(x['title'])}">
<img loading="lazy" src="{thumb_url(x, pre)}" alt="" width="96" height="96">
</a>''' for x in alts)
    alt_block = f'''<div class="category-alt-games">
<span class="side-title">Try next</span>
<div>{alt_links}</div>
</div>''' if alt_links else ''
    return f'''<section class="category-player">
<div class="stage"><img class="stage-preview-img" src="{thumb_url(g, pre)}" alt="{esc(g['title'])} online game screenshot" width="640" height="640"><iframe src="{esc(g['url'])}" title="{esc(g['title'])}" allow="autoplay; fullscreen; gamepad; keyboard-map; xr-spatial-tracking; cross-origin-isolated" allowfullscreen></iframe></div>
<div class="category-player-copy">
<div class="category-player-text">
<span class="side-title">Featured game</span>
<h2>Play {esc(g['title'])}</h2>
<p>{esc(g['desc'])}</p>
<a class="btn btn-primary" href="{game_url(g, pre)}">Open full game page</a>
</div>
{alt_block}
</div>
</section>'''

def page_redirects():
    redirects = [
        {'from': f'/{slug}/', 'to': '/', 'status': 301}
        for slug in sorted(REMOVED_GAME_SLUGS)
    ]
    redirects += [
        {'from': f'/games/{src}/', 'to': f'/games/{dst}/', 'status': 301}
        for src, dst in sorted(REMOVED_CATEGORY_REDIRECTS.items())
        if src not in CATS
    ]
    worker_dir = os.path.join(BASE, 'worker')
    os.makedirs(worker_dir, exist_ok=True)
    with open(os.path.join(worker_dir, 'redirects.json'), 'w', encoding='utf-8') as f:
        json.dump(redirects, f, indent=2)
        f.write('\n')

def page_list(slug, h1, blurb, games, seo, canonical, active=''):
    pre = '../' * (slug.count('/') + 1)
    cards = ''.join(game_card(g, pre) for g in games)
    page_title = f'{h1} — Play Free Online | {SITE_NAME}'
    meta_desc = blurb[:155]
    topic_block = ''
    if canonical == 'games/slope/':
        page_title = f'Slope Games - Games Like Speed Slope | {SITE_NAME}'
        meta_desc = 'Play slope games online, including games like Speed Slope with fast 3D movement, quick reflexes, rolling challenges and instant browser play.'
        topic_block = f'''<section class="content-block">
<h2>Games Like Speed Slope</h2>
<p>Slope games are fast browser games built around momentum, reaction time and narrow margins for error. If you searched for games like Speed Slope, start with rolling, racing and runner games that ask you to read the path early, make small corrections and restart quickly after a crash.</p>
<p>This collection stays focused on 3D reflex games instead of mixing in unrelated sports, card or quiz pages. That makes it easier to find another game with the same speed, obstacle-dodging and one-more-run feeling as Speed Slope.</p>
</section>'''
    extra = f'<script type="application/ld+json">{json.dumps(item_list_ld(h1, canonical, games))}</script>'
    og_image = 'assets/thumbs/' + thumb_file(games[0]) if games else None
    html_doc = head(page_title, meta_desc, pre, canonical, extra=extra, og_image=og_image)
    html_doc += header(pre, active)
    html_doc += f'''<main class="container">
<div class="page-head"><h1>{esc(h1)} <span class="tick">.</span></h1><p>{esc(blurb)}</p></div>
{category_player(canonical, pre, games)}
{sort_bar()}
<div class="game-grid" id="sortGrid">{cards}</div>
<div class="load-more-wrap" id="loadMoreWrap"><button class="btn btn-ghost btn-lg" id="loadMore">Load more games</button></div>
{topic_block}
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


def page_admin_comments():
    pre = '../../'
    html_doc = head(f'Comment Moderation | {SITE_NAME}', 'Review submitted comments.', pre, 'admin/comments/', ads=False).replace(
        'index,follow,max-image-preview:large', 'noindex,nofollow'
    )
    html_doc += header(pre)
    html_doc += '''<main class="container">
<div class="page-head"><h1>Comment Moderation <span class="tick">.</span></h1><p>Review pending comments and keep spam off the site.</p></div>
<section class="content-block admin-comments" id="adminComments">
<div class="list-toolbar"><button class="sort-btn active" data-status="pending">Pending</button><button class="sort-btn" data-status="approved">Approved</button><button class="sort-btn" data-status="rejected">Rejected</button><button class="sort-btn" data-status="hidden">Hidden</button><span class="result-count" id="adminCommentCount"></span></div>
<div id="adminCommentList" class="comments-list"><p class="comment-note">Loading comments...</p></div>
</section>
</main>'''
    html_doc += footer(pre)
    write('admin/comments/index.html', html_doc)


def yaml_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def cms_config_yml():
    category_options = '\n'.join(
        f'          - {{ label: {yaml_quote(label)}, value: {yaml_quote(slug)} }}'
        for slug, (label, _) in sorted(ALL_CATS.items())
    )
    return f'''# yaml-language-server: $schema=https://unpkg.com/@sveltia/cms/schema/sveltia-cms.json
backend:
  name: github
  repo: saralaaga/speed-slope-playorbit
  branch: main

media_folder: app/assets/uploads
public_folder: /assets/uploads

collections:
  - name: sites
    label: Sites
    files:
      - name: speedslope_net
        label: SpeedSlope.net
        file: cms-data/sites/speedslope-net.json
        format: json
        fields:
          - {{ label: Site Name, name: site_name, widget: string }}
          - {{ label: Site URL, name: site_url, widget: string }}
          - {{ label: Site Slug, name: slug, widget: string, required: false }}
          - {{ label: Domain, name: domain, widget: string, required: false }}
          - {{ label: Tagline, name: tagline, widget: text }}
          - {{ label: Launch Mode, name: launch_mode, widget: select, options: [single, portal, slugs] }}
          - {{ label: Launch Game Slug, name: launch_game_slug, widget: string, required: false }}
          - {{ label: Home Game Slug, name: home_game_slug, widget: string, required: false }}
          - label: Published Game Slugs
            name: published_game_slugs
            widget: list
            required: false
            field: {{ label: Game Slug, name: slug, widget: string }}
          - {{ label: Contact Email, name: contact_email, widget: string }}
          - {{ label: Games Email, name: games_email, widget: string }}
          - {{ label: Legal Email, name: legal_email, widget: string }}
          - {{ label: Ads Enabled, name: ads_enabled, widget: boolean, default: false }}
          - {{ label: AdSense Client, name: adsense_client, widget: string, required: false, hint: "AdSense ca-pub id, e.g. ca-pub-1234567890123456" }}
          - {{ label: Aggregate Rating Schema, name: include_aggregate_rating_schema, widget: boolean, default: false }}
          - {{ label: Turnstile Site Key, name: turnstile_site_key, widget: string, required: false }}

  - name: games
    label: Games
    folder: cms-data/games
    extension: json
    format: json
    create: true
    slug: "{{{{slug}}}}"
    identifier_field: title
    summary: "{{{{title}}}} · {{{{slug}}}}"
    sortable_fields: [title, slug, plays, rating, added, sort_order]
    fields:
      - {{ label: Sort Order, name: sort_order, widget: number, value_type: int, required: false }}
      - {{ label: Title, name: title, widget: string }}
      - {{ label: Slug, name: slug, widget: string }}
      - {{ label: Iframe URL, name: url, widget: string }}
      - label: Categories
        name: cats
        widget: select
        multiple: true
        options:
{category_options}
      - label: Tags
        name: tags
        widget: list
        required: false
        field: {{ label: Tag, name: tag, widget: string }}
      - {{ label: Rating, name: rating, widget: number, value_type: float, min: 1, max: 5 }}
      - {{ label: Plays, name: plays, widget: number, value_type: int, min: 0 }}
      - {{ label: Hot, name: hot, widget: boolean, default: false }}
      - {{ label: New, name: "new", widget: boolean, default: false }}
      - {{ label: Added Date, name: added, widget: string, required: false }}
      - {{ label: SEO Title, name: seo_title, widget: string, required: false }}
      - {{ label: Meta Description, name: meta_desc, widget: text, required: false }}
      - {{ label: Description, name: desc, widget: text }}
      - label: How To Play
        name: howto
        widget: list
        required: false
        field: {{ label: Step, name: step, widget: string }}
      - label: Controls
        name: controls
        widget: list
        required: false
        fields:
          - {{ label: Key, name: key, widget: string }}
          - {{ label: Action, name: action, widget: string }}
      - label: Tips
        name: tips
        widget: list
        required: false
        field: {{ label: Tip, name: tip, widget: string }}
      - label: FAQs
        name: faqs
        widget: list
        required: false
        fields:
          - {{ label: Question, name: question, widget: string }}
          - {{ label: Answer, name: answer, widget: text }}
      - {{ label: Embed Source, name: embed_source, widget: string, required: false }}
      - {{ label: Thumbnail URL, name: thumb_url, widget: string, required: false }}

  - name: categories
    label: Categories
    folder: cms-data/categories
    extension: json
    format: json
    create: true
    slug: "{{{{slug}}}}"
    identifier_field: name
    fields:
      - {{ label: Name, name: name, widget: string }}
      - {{ label: Slug, name: slug, widget: string }}
      - {{ label: Active, name: active, widget: boolean, default: true }}
'''


def page_admin_cms():
    html_doc = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Content CMS</title>
</head>
<body>
<script src="https://unpkg.com/@sveltia/cms/dist/sveltia-cms.js"></script>
</body>
</html>'''
    redirect_doc = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0; url=../">
<title>Content CMS</title>
</head>
<body><a href="../">Open Content CMS</a></body>
</html>'''
    write('admin/index.html', html_doc)
    write('admin/config.yml', cms_config_yml())
    write('admin/cms/index.html', redirect_doc)


# ============================================================ static content
ABOUT = f'''<p>{SITE_NAME} is a free browser-games portal. We hand-pick lightweight HTML5 games — basketball, sports, racing, puzzles, arcade classics and more — and make each one playable in a single click, with no downloads, no installs and no accounts.</p>
<h2>What we do</h2>
<ul><li>Curate and test every game before it goes live.</li><li>Write original guides, controls and tips for each title.</li><li>Keep the site fast: the game loads automatically the moment you open the page.</li></ul>
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
    os.makedirs(os.path.join(ROOT, 'assets', 'uploads'), exist_ok=True)
    for g in G:
        if 'thumbfile' not in g: make_thumb(g)

    favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#b9f226"/><path d="M26 20l18 12-18 12z" fill="#111503"/></svg>'''
    write('assets/favicon.svg', favicon)
    make_icon_png(os.path.join(ROOT, 'assets', 'favicon-48x48.png'), 48)
    make_icon_png(os.path.join(ROOT, 'assets', 'apple-touch-icon.png'), 180)
    write('site.webmanifest', json.dumps({"name": SITE_NAME, "short_name": "SpeedSlope", "icons": [
        {"src": "assets/favicon-48x48.png", "sizes": "48x48", "type": "image/png"},
        {"src": "assets/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}
    ], "theme_color": "#b9f226", "background_color": "#0a0d07", "display": "browser"}, indent=1))

    page_home()
    for g in G: page_game(g)

    for c, (name, blurb) in CATS.items():
        games = sorted([g for g in G if c in g['cats']], key=lambda x: -x['plays'])
        if c == 'slope':
            seo = (f'Play slope games online on {SITE_NAME}, including games like Speed Slope with 3D movement, fast restarts, '
                   f'obstacle dodging and reflex-based control. These free browser games are selected for players who want speed, '
                   f'rolling, racing or runner challenges without downloads or sign-ups.')
        else:
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
    page_admin_comments()
    page_admin_cms()

    # games.json (root-relative; search page prefixes its own depth)
    data = [dict(title=g['title'], slug=g['slug'], url=game_url(g, ''),
                 thumb='assets/thumbs/' + thumb_file(g), categories=[CATS[c][0] for c in g['cats']],
                 tags=g['tags'], rating=g['rating'], plays=g['plays'], isHot=g['hot'], isNew=g['new'])
            for g in G]
    write('games.json', json.dumps(data, ensure_ascii=False, indent=1))

    # sitemap + robots
    home_slug = home_game()['slug']
    game_urls = [] if CONFIG.get('launch_mode', 'single') == 'single' else [f'{g["slug"]}/' for g in G if g['slug'] != home_slug]
    urls = [''] + game_urls + [f'games/{c}/' for c in CATS] + \
           ['hot-games/', 'new-games/', 'search/', 'about/', 'contact/', 'privacy/', 'terms/', 'dmca/']
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pri = '1.0' if u == '' else ('0.8' if not u.startswith('games/') else '0.6')
        sm.append(f'<url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY}</lastmod><priority>{pri}</priority></url>')
    sm.append('</urlset>')
    write('sitemap.xml', '\n'.join(sm))
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n')
    if ADSENSE_CLIENT and ADSENSE_CLIENT.startswith('ca-'):
        write('ads.txt', f'google.com, {ADSENSE_CLIENT[3:]}, DIRECT, f08c47fec0942fa0\n')
    page_redirects()

    n = sum(len(fs) for _, _, fs in os.walk(ROOT))
    print(f'OK — {len(G)} games, {len(CATS)} categories, {n} files total')

if __name__ == '__main__':
    main()
