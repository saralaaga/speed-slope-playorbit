# SpeedSlope.net Static Game Site

This project is a static site generator for a browser-game portal. It keeps the
full catalog in `games_data.json`, then publishes only the game set selected in
`site_config.json`.

## Local Preview

```sh
python3 build_site.py
python3 validate_site.py
python3 -m http.server 8123 --directory app
```

Open `http://127.0.0.1:8123/speed-slope/`.

## Current Launch Shape

The project is configured for a single-game launch:

- `launch_mode`: `single`
- `launch_game_slug`: `speed-slope`

This produces a focused site with:

- Home page that IS the play page: the game iframe loads automatically on
  open, no "Play" click needed
- The game slug URL (`/speed-slope/`) redirects to the home page (noindex,
  canonical points at `/`) to avoid duplicate content
- Category pages for that game's categories
- Search, hot, new, about, contact, privacy, terms and DMCA pages
- `games.json`, `sitemap.xml` and `robots.txt`

## Build

```sh
python3 build_site.py
python3 validate_site.py
```

`build_site.py` cleans old generated pages before each build while preserving
`app/assets/`, so stale game pages are not carried into the next deployment.

## Current Game Source

The Speed Slope page is configured with the public embed URL exposed by the
1000Games and AZGames game pages:

- Primary source page: `https://1000games.io/speed-slope`
- Additional source page: `https://azgames.io/speed-slope`
- Embed URL used by this site: `https://gamea.azgame.io/speed-slope/`

Both source pages expose the same game iframe. The `gamea.azgame.io` game HTML
also points its canonical URL at 1000Games. Before a production launch, confirm
usage with the publisher (`support@1000games.io`) or rights holder so the game
iframe is a stable, authorized dependency.

## Add More Games Later

To publish a hand-picked set, change `site_config.json`:

```json
{
  "launch_mode": "slugs",
  "published_game_slugs": [
    "basketball-stars-2026",
    "basketball-fever"
  ]
}
```

To publish the whole catalog:

```json
{
  "launch_mode": "portal"
}
```

Then rebuild and validate.

## Production Checklist

- Replace `site_url` and all contact emails in `site_config.json`.
- Confirm publisher/embedding rights for every game before publishing it.
- Keep `ads_enabled` disabled until real ad code is ready; disabled ads do not
  render placeholder boxes.
- Keep `include_aggregate_rating_schema` disabled until ratings and vote counts
  come from a trustworthy first-party source.
- Run `validate_site.py` before uploading `app/`.

## License

MIT. Game assets and embedded games remain the property of their respective
rights holders.
