# AGENTS.md

## Project

SpeedSlope.net is a generated static browser-game portal. The production site is the contents of `app/` after running `build_site.py`.

## Local Machine Rules (user directive 2026-10-07)

- Any browser automation must go through **ego lite** (`ego-browser` CLI / the `ego-browser` skill). Do NOT drive the user's Google Chrome, do NOT open windows or tabs in it, and never take over the user's screen focus. The user works on this machine concurrently ("不要和我抢电脑").
- Headless Playwright via the uv interpreter is fine for the availability gate (it owns no visible window).
- Cloudflare dashboard changes: prefer handing off to the user (they keep a logged-in session) or use ego lite after the user logs in there once.

## Build And Validate

Run this before every deploy:

```sh
python3 build_site.py
python3 validate_site.py
```

### Required Game Availability Gate

This is mandatory for every new or replaced game before deploy. Run the browser availability check against every changed game slug, including any game chosen as a featured category player. Do not rely on HTTP status checks; GameDistribution can return a working shell page and then redirect the runtime iframe to a blocked page.

```sh
node check_game_availability.js new-game-slug another-new-game
```

A game must not be published if the check detects any of these signals:

- iframe redirects to `blocked.html`
- iframe URL contains `unregistered=true`
- game frame shows `not available here` or `Click here to Play`
- iframe returns 403 or fails to load after clicking Play

When a game fails, add its slug to `REMOVED_GAME_SLUGS`, rebuild, and confirm it no longer appears in category pages, `app/games.json`, or `app/sitemap.xml`. If a removed category page would otherwise remain from an older deploy, add it to `REMOVED_CATEGORY_REDIRECTS`.

After deploy, rerun the same check against the production domain or the Worker preview URL before considering the release complete:

```sh
SITE_BASE_URL=https://speedslope.net node check_game_availability.js new-game-slug another-new-game
```

If the npm playwright package is unavailable, run the committed Python port with the uv-managed interpreter instead:

```sh
SITE_BASE_URL=http://127.0.0.1:8000 /Users/carlos/.local/share/uv/tools/playwright/bin/python check_availability_py.py new-game-slug
```

The apex domain sits behind zone-level bot protection that challenges automated clients (curl, headless Chromium); for post-deploy verification use the Worker preview URL (`https://speedslope-net.saralaagarwal1990.workers.dev`), which serves the same deployed assets without the zone firewall. The checker treats Cloudflare interstitials ("Just a moment...", "Attention Required!") as failures.

A successful build currently reports `174 games, 23 categories, 422 files total`.

## Production Hosting

The site is deployed as a Cloudflare Worker with Workers Static Assets.

- Cloudflare Worker: `speedslope-net`
- Production domains: `https://speedslope.net`, `https://www.speedslope.net`
- Worker entry point: `worker/index.mjs`
- Static asset directory: `app/`
- Site URL configured in `site_config.json`: `https://speedslope.net`

## Deployment

Continuous deployment runs through GitHub Actions.

- Workflow: `.github/workflows/deploy.yml`, triggered by push to `main` (and manual dispatch)
- Required repository secrets: `CLOUDFLARE_API_TOKEN` (Workers Scripts: Edit and D1: Edit) and `CLOUDFLARE_ACCOUNT_ID`
- The workflow builds, runs Worker/filter tests, validates the output, then runs `wrangler deploy`
- Keep the game availability gate for changed iframe URLs before merging
- The D1 comments database is a separate runtime resource; do not change or migrate it as part of a normal static content deploy
- `app/_redirects` is not supported by Workers Static Assets; legacy redirects are generated into `worker/redirects.json` and handled by the Worker

## AdSense

- `adsense_client` in `site_config.json` (and `cms-data/sites/speedslope-net.json`, which the CMS edits and the build prefers) holds the AdSense `ca-pub-…` id.
- When it is set, `build_site.py` writes the AdSense loader + `google-adsense-account` meta into the `<head>` of every public page, plus `app/ads.txt`. It is independent of `ads_enabled`, so site verification works before ad slots are switched on.
- Noindex admin pages (`/admin/`, `/admin/cms/`, `/admin/comments/`) intentionally omit the loader.
