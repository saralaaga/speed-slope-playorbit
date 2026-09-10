# Git-Backed CMS POC

SpeedSlope now has a minimal Sveltia CMS proof of concept for editing site and game content as repository files.

## What It Adds

- CMS entry point: `/admin/`
- CMS config generated at: `/admin/config.yml`
- Editable data source:
  - `cms-data/sites/speedslope-net.json`
  - `cms-data/games/*.json`
  - `cms-data/categories/*.json`

`build_site.py` and `validate_site.py` prefer `cms-data/` when it exists. If `cms-data/` is removed, they fall back to the legacy `site_config.json` and `games_data.json` files.

## Local Editing

Run a local static server after building:

```sh
python3 build_site.py
python3 -m http.server 8080 --directory app
```

Open this in a Chromium-based browser:

```text
http://localhost:8080/admin/index.html
```

Use Sveltia CMS's local repository workflow and select the project root folder when prompted. Sveltia writes directly to local files; commit changes with Git after reviewing the diff.

## Production Editing

The CMS is configured for the current GitHub repository:

```yaml
backend:
  name: github
  repo: saralaaga/speed-slope-playorbit
  branch: main
```

For simple production use, sign in with a GitHub personal access token from the Sveltia login screen. For non-technical editors, deploy the Sveltia CMS Authenticator or another Decap-compatible OAuth helper, then add its `base_url` to the CMS backend config.

Cloudflare Access should continue protecting `/admin/*`.

## Data Sync

To regenerate `cms-data/` from the legacy JSON files:

```sh
python3 scripts/sync_cms_data.py
```

This is a migration/sync helper. Once editing moves fully to the CMS, treat `cms-data/` as the source of truth.

## Notes

This POC intentionally avoids a custom database-backed admin. It keeps the static site generator, Cloudflare Pages deployment, and existing D1 comments system intact.
