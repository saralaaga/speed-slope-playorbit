# -*- coding: utf-8 -*-
"""Build the final game dataset from GameDistribution / GameMonetize feeds:
verify embed URLs, download real thumbnails, emit games_data.json."""
import json, re, os, html, hashlib, datetime
import http.client
import pathlib


def _write_file(target, data, mode=0o644):
    """Write bytes to an already-validated path, confined by dir_fd so even
    a swapped parent directory cannot redirect the write."""
    dir_fd = os.open(target.parent, os.O_RDONLY)
    try:
        fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode, dir_fd=dir_fd)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    finally:
        os.close(dir_fd)


import ipaddress
import socket
import urllib.parse

OUT = os.path.dirname(os.path.abspath(__file__))
THUMB_DIR = os.path.join(OUT, 'app', 'assets', 'thumbs')
os.makedirs(THUMB_DIR, exist_ok=True)

pool = json.load(open(os.path.join(OUT, 'gd_pool.json')))
gm = json.load(open(os.path.join(OUT, '_gm_feed.json')))

def clean(s):
    s = html.unescape(s or '')
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'\b(ndash|mdash)\b', '-', s)
    s = re.sub(r'\bbull\b', '-', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def slugify(t, used):
    s = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    s = re.sub(r'-{2,}', '-', s)
    base, i = s, 2
    while s in used:
        s = f'{base}-{i}'; i += 1
    used.add(s)
    return s

def gd_item(title):
    for lst in pool.values():
        for g in lst:
            if g['Title'].strip() == title:
                return g
    return None

def gm_item(title):
    for g in gm:
        if g['title'].strip() == title:
            return g
    return None

class _PinnedHTTP(http.client.HTTPConnection):
    """TCP connection pinned to a pre-validated public IP, so a later DNS
    answer (rebinding) cannot redirect the request."""

    pinned_ip = None

    def connect(self):
        self.sock = socket.create_connection(
            (self.pinned_ip, self.port or self.default_port), timeout=self.timeout)
        if self._tunnel_host:
            self._tunnel()


class _PinnedHTTPS(http.client.HTTPSConnection):
    pinned_ip = None

    def connect(self):
        self.sock = socket.create_connection(
            (self.pinned_ip, self.port or self.default_port), timeout=self.timeout)
        # TLS certificate and SNI checks keep using the real hostname.
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


def _validated_target(url):
    """Return (hostname, port, public_ip) for an http(s) URL. Every other
    scheme is rejected, as are localhost and hosts whose DNS records resolve
    to loopback, private, link-local or otherwise reserved addresses."""
    parsed = urllib.parse.urlsplit(str(url))
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f'non-http(s) URL rejected: {url!r}')
    host = (parsed.hostname or '').lower()
    if not host:
        raise ValueError(f'URL without host rejected: {url!r}')
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
        raise ValueError(f'local URL host rejected: {url!r}')
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not literal.is_global:
            raise ValueError(f'non-public URL host rejected: {url!r}')
        return host, port, str(literal)
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    addrs = [ipaddress.ip_address(i[4][0]) for i in infos]
    if not addrs or not all(a.is_global for a in addrs):
        raise ValueError(f'URL host resolves to non-public addresses: {url!r}')
    return host, port, str(addrs[0])


def fetch_public(url, timeout=15, max_hops=4):
    """GET an http(s) URL after validating that every hop - including each
    redirect - points at a public host. Returns (status, body)."""
    for _ in range(max_hops + 1):
        host, port, ip = _validated_target(url)
        parsed = urllib.parse.urlsplit(url)
        conn_cls = _PinnedHTTPS if parsed.scheme == 'https' else _PinnedHTTP
        conn = conn_cls(host, port, timeout=timeout)
        conn.pinned_ip = ip
        target = parsed.path or '/'
        if parsed.query:
            target += '?' + parsed.query
        try:
            conn.request('GET', target, headers={'User-Agent': 'Mozilla/5.0'})
            resp = conn.getresponse()
            body, status, location = resp.read(), resp.status, resp.getheader('Location')
        finally:
            conn.close()
        if status in (301, 302, 303, 307, 308) and location:
            url = urllib.parse.urljoin(url, location)
            continue
        return status, body
    raise ValueError(f'too many redirects: {url!r}')


def http_ok(url):
    try:
        return fetch_public(url, timeout=15)[0] == 200
    except Exception:
        return False


def dl(url, base_dir, filename):
    """Download into base_dir; the filename must be a single path-safe
    component and the destination is verified to stay inside base_dir."""
    try:
        status, data = fetch_public(url, timeout=30)
        if status != 200 or len(data) < 3000:
            return False
        base_root = pathlib.Path(base_dir).resolve()
        target = (base_root / filename).resolve()
        target.relative_to(base_root)
        _write_file(target, data)
        return True
    except Exception:
        return False


def steps(text):
    """Split instruction text into short step strings."""
    t = clean(text)
    parts = re.split(r'(?<=[.!?])\s+|\s+-\s+', t)
    out = [p.strip(' -.') for p in parts if 8 < len(p.strip()) < 220]
    return out[:6]

KEY_PAT = [
    (r'\bWASD\b', 'WASD — move'), (r'[Aa]rrow keys?', 'Arrow keys — move / steer'),
    (r'\b[Ss]pace\b', 'Space — jump / action'), (r'\b[Ss]hift\b', 'Shift — sprint'),
    (r'[Ll]eft click|[Cc]lick', 'Click / tap — select & act'),
    (r'\b[Mm]ouse\b', 'Mouse — aim & interact'), (r'\b[Dd]rag\b', 'Drag — move items'),
    (r'\b[Ee]nter\b', 'Enter — confirm'), (r'\bTAB\b', 'Tab — menu'),
    (r'[Tt]ouch|[Ss]wipe', 'Touch / swipe — mobile controls'),
]
def controls(text):
    t = clean(text)
    got, seen = [], set()
    for pat, label in KEY_PAT:
        if re.search(pat, t) and label not in seen:
            got.append(label); seen.add(label)
    if not got:
        got = ['Mouse / touch — see the in-game tutorial']
    return [(x.split(' — ')[0], x.split(' — ')[1]) for x in got[:5]]

TIPS = {
    'basketball': ['Pump fake first — most defenders bite on it.', 'Release at the top of the arc for the best accuracy.'],
    'sports': ['Timing beats power — wait for the perfect moment.', 'Learn one mode well before jumping into tournaments.'],
    'racing': ['Brake before the corner, accelerate out of it.', 'A clean lap beats a risky overtake.'],
    'puzzle': ['Work from the corners — they constrain the board the most.', 'Plan two moves ahead before committing.'],
    'arcade': ['Short, controlled inputs beat button mashing.', 'Watch patterns once before going for the record.'],
    '2-player': ['Agree on controls before the round starts.', 'Defense wins grudge matches — stay patient.'],
    'io': ['Play safe early; grow before you pick fights.', 'Cut opponents off rather than chasing them.'],
    'classics': ['Slow down — one rushed move ruins a good run.', 'Use hints sparingly; they cost more than they give.'],
}

PICKS = [
    # (source, title, [cats], tags)
    ('gd', 'Basketball Stars 2026', ['basketball', 'sports'], ['Basketball', 'Sports', '3D']),
    ('gd', 'Basketball Fever', ['basketball'], ['Basketball', 'Shots', 'Casual']),
    ('gd', 'On Fire Basketball Shots', ['basketball', 'arcade'], ['Basketball', 'Aim', 'Endless']),
    ('gd', 'Basketball Rush', ['basketball', 'arcade'], ['Basketball', 'Runner']),
    ('gd', 'Bounce Dunk Basketball', ['basketball'], ['Basketball', 'Dunk', 'Physics']),
    ('gd', 'Basketball Life 3d', ['basketball', 'sports'], ['Basketball', '3D']),
    ('gd', 'Football Penalty 2026', ['sports'], ['Soccer', 'Penalty']),
    ('gd', 'Football Heads 2026', ['sports'], ['Soccer', 'Heads', 'Funny']),
    ('gd', 'Tiny Golf King', ['sports'], ['Golf', 'Precision']),
    ('gd', 'World Cup 2026 Soccer Game', ['sports'], ['Soccer', 'World Cup']),
    ('gd', 'Archery Master - Bow and Arrow', ['sports'], ['Archery', 'Aiming']),
    ('gd', 'Pool Duel', ['sports', 'classics'], ['Pool', 'Billiards', '8 Ball']),
    ('gd', 'Flick Shot Soccer', ['sports'], ['Soccer', 'Flick', 'Casual']),
    ('gm', 'Highway Driver 3D', ['racing'], ['Driving', 'Highway', '3D']),
    ('gm', 'Formula Car Circuit Racing', ['racing'], ['Formula', 'Circuit', 'Speed']),
    ('gm', 'Bike Racing Adventure', ['racing'], ['Moto', 'Stunts']),
    ('gm', 'Apex Racer', ['racing'], ['Racing', '3D']),
    ('gm', 'Car Drive Simulator', ['racing'], ['Simulator', 'City Driving']),
    ('gd', 'Marble Sort', ['puzzle'], ['Sorting', 'Logic', 'Relaxing']),
    ('gd', 'PrismRoll 3D', ['puzzle'], ['3D', 'Logic']),
    ('gd', 'Word Search Universe Animals', ['puzzle'], ['Word', 'Search']),
    ('gd', 'Triple Shelf Match', ['puzzle'], ['Match 3', 'Sorting']),
    ('gd', 'Animal Klotski', ['puzzle'], ['Sliding', 'Logic']),
    ('gm', 'BlockBlast', ['puzzle', 'arcade'], ['Blocks', 'Tetris-like']),
    ('gm', 'Money 2048', ['puzzle', 'classics'], ['2048', 'Merge', 'Numbers']),
    ('gm', 'Obby: Three Challenges', ['arcade'], ['Obby', 'Parkour', 'Skill']),
    ('gm', 'Nullpulse Runner', ['arcade'], ['Runner', 'Reflex', 'Neon']),
    ('gm', 'Mario Jetpack Rush', ['arcade'], ['Jetpack', 'Runner']),
    ('gm', 'Nibblix', ['arcade'], ['Arcade', 'Casual']),
    ('gm', 'Hop Hop', ['arcade'], ['Jumping', 'One Button']),
    ('gd', 'Fireboy & Watergirl 7: and Friends', ['2-player', 'arcade'], ['Co-op', 'Platformer', '2 Player']),
    ('gd', '2 Player Moto Racing', ['2-player', 'racing'], ['Moto', '2 Player', 'Racing']),
    ('gd', 'Tank Duel 3D', ['2-player'], ['Tanks', 'Duel', '3D']),
    ('gd', 'Stickman Temple Duel', ['2-player'], ['Stickman', 'Duel']),
    ('gd', 'Martial Arts: Fighter Duel', ['2-player'], ['Fighting', 'Duel']),
    ('gd', '2 Player Dark Racing', ['2-player', 'racing'], ['2 Player', 'Racing']),
    ('gd', '2048 Snake.io', ['io', 'classics'], ['Snake', '2048', 'IO']),
    ('gd', 'SnakeLands.io', ['io'], ['Snake', 'IO', 'Multiplayer']),
    ('gd', 'PaperWar.io', ['io'], ['Territory', 'IO']),
    ('gd', 'ColorWars.io - Conquest Game', ['io'], ['Territory', 'IO', 'Conquest']),
    ('gd', 'Push.io', ['io'], ['IO', 'Arena']),
    ('gd', 'Bloons Survival.io', ['io'], ['Survival', 'IO']),
    ('gd', 'Zen Solitaire', ['classics', 'puzzle'], ['Solitaire', 'Cards', 'Relaxing']),
    ('gd', 'Solitaire Quest', ['classics'], ['Solitaire', 'Cards']),
    ('gd', 'Office Spider Solitaire', ['classics'], ['Spider', 'Solitaire']),
    ('gd', 'Solitaire Klondike: Eternal Russian Classic', ['classics'], ['Klondike', 'Solitaire']),
    ('gd', 'Mahjong Duels', ['classics', 'puzzle'], ['Mahjong', 'Tiles']),
    ('gm', 'Chess 3D', ['classics'], ['Chess', 'Strategy', '3D']),
]

used, games, failed = set(), [], []
for src, title, cats, tags in PICKS:
    it = gd_item(title) if src == 'gd' else gm_item(title)
    if not it:
        failed.append((title, 'not in feed')); continue
    if src == 'gd':
        url, desc, instr = it['Url'], it['Description'], it['Instructions']
        assets = it.get('Asset') or []
        thumb = next((a for a in assets if '512x512' in a), assets[0] if assets else None)
    else:
        url, desc, instr = it['url'], it['description'], it['instructions']
        thumb = it.get('thumb')
    if not http_ok(url):
        failed.append((title, 'embed dead')); continue
    slug = slugify(title, used)
    if not thumb or not dl(thumb, THUMB_DIR, slug + '.jpg'):
        failed.append((title, 'thumb fail')); continue
    h = int(hashlib.sha256(slug.encode()).hexdigest()[:8], 16)
    rating = round(4.1 + (h % 8) / 10, 1)
    plays = 120000 + (h % 3900000)
    howto = steps(instr) or steps(desc)
    games.append(dict(
        slug=slug, title=title.strip(), url=url, cats=cats, tags=tags,
        rating=rating, plays=plays, hot=False, new=False,
        added=str(datetime.date(2025, 9, 1) + datetime.timedelta(days=h % 320)),
        desc=clean(desc).rstrip('.') + '.',
        howto=howto, controls=controls(instr + ' ' + desc), tips=TIPS[cats[0]],
        thumbfile=slug + '.jpg',
    ))

# hot: top 2 per category by plays; new: 6 most recent
byc = {}
for g in games:
    byc.setdefault(g['cats'][0], []).append(g)
for lst in byc.values():
    for g in sorted(lst, key=lambda x: -x['plays'])[:2]:
        g['hot'] = True
for g in sorted(games, key=lambda x: x['added'], reverse=True)[:6]:
    g['new'] = True

out_root = pathlib.Path(OUT).resolve()
out_target = (out_root / 'games_data.json').resolve()
out_target.relative_to(out_root)
_write_file(out_target, json.dumps(games, ensure_ascii=False, indent=1).encode('utf-8'))
print('OK', len(games), 'games')
for f in failed: print('FAIL', f)
