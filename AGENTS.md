# AGENTS.md

## Project

SpeedSlope.net is a generated static browser-game portal. The production site is the contents of `app/` after running `build_site.py`.

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

When a game fails, add its slug to `REMOVED_GAME_SLUGS`, rebuild, and confirm it no longer appears in category pages, `app/games.json`, or `app/sitemap.xml`. If a removed category page would otherwise remain on Cloudflare Pages from an older deploy, add it to `REMOVED_CATEGORY_REDIRECTS`.

After deploy, rerun the same check against the production domain or the Pages preview URL before considering the release complete:

```sh
SITE_BASE_URL=https://speedslope.net node check_game_availability.js new-game-slug another-new-game
```

A successful build currently reports `131 games, 19 categories, 331 files total`.

## Production Hosting

The site is deployed on Cloudflare Pages.

- Cloudflare Pages project: `speedslope-net`
- Production domains: `https://speedslope.net`, `https://www.speedslope.net`
- Pages preview domain: `https://speedslope-net.pages.dev`
- Publish directory: `app/`
- Site URL configured in `site_config.json`: `https://speedslope.net`

## Deployment

Cloudflare Pages handles production deployment from the `main` branch through its native Git integration.

- Project: `speedslope-net`
- Output directory: `app/`
- Production domains: `https://speedslope.net`, `https://www.speedslope.net`
- GitHub Actions, Deploy Hooks, and Wrangler are not production deployment paths.
- Keep the game availability gate for changed iframe URLs before merging.
- The D1 comments database is a separate runtime resource; do not change or migrate it as part of a normal static content deploy.
