# AGENTS.md

## Project

SpeedSlope.net is a generated static browser-game portal. The production site is the contents of `app/` after running `build_site.py`.

## Build And Validate

Run this before every deploy:

```sh
python3 build_site.py
python3 validate_site.py
```

Before publishing new games, open them on `https://speedslope.net/<slug>/`, click `Play Now`, and remove any game whose iframe redirects to `blocked.html`, shows `not available here`, returns `unregistered=true`, or fails with 403. Do not keep externally blocked games in the catalog.

A successful build currently reports `37 games, 27 categories, 116 files total`.

## Production Hosting

The site is deployed on Cloudflare Pages.

- Cloudflare Pages project: `speedslope-net`
- Production domains: `https://speedslope.net`, `https://www.speedslope.net`
- Pages preview domain: `https://speedslope-net.pages.dev`
- Publish directory: `app/`
- Site URL configured in `site_config.json`: `https://speedslope.net`

## Cloudflare Credentials

Cloudflare credentials are stored in Bitwarden Secrets Manager and are accessed with `bws`.

- bws environment file: `/Users/carlos/Coding/Taskstick/.env.local.md`
- Required bws secrets:
  - `CLOUDFLARE_API_TOKEN`
  - `CLOUDFLARE_ACCOUNT_ID`

Do not print secret values in logs. Load them into the shell environment only:

```sh
set -a
. /Users/carlos/Coding/Taskstick/.env.local.md
set +a

export CLOUDFLARE_API_TOKEN="$(bws secret get "$(bws secret list | jq -r '.[] | select(.key == "CLOUDFLARE_API_TOKEN") | .id')" | jq -r '.value')"
export CLOUDFLARE_ACCOUNT_ID="$(bws secret get "$(bws secret list | jq -r '.[] | select(.key == "CLOUDFLARE_ACCOUNT_ID") | .id')" | jq -r '.value')"
```

## Deploy

Deploy the static output directly to Cloudflare Pages:

```sh
python3 build_site.py
python3 validate_site.py

npx wrangler pages deploy app \
  --project-name=speedslope-net \
  --commit-dirty=true \
  --commit-message="Publish SpeedSlope portal refresh"
```

The deploy completed successfully in this session with Wrangler `4.126.0` and returned:

```text
https://a897ce3f.speedslope-net.pages.dev
```

The production domain was verified after deploy by fetching `https://speedslope.net/games/archery/` and confirming the new category player and newly added games were present.
