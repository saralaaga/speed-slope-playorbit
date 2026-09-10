# Deployment

SpeedSlope is a generated Cloudflare Pages site with Pages Functions and a D1 comments binding.

## Flow

```text
local build/validate/game check
  -> push main
  -> Cloudflare Pages Git integration builds app/
  -> Pages Functions and static files publish together
```

Production deployment uses Cloudflare Pages native Git integration. There is no project Deploy Hook, GitHub deployment secret, or normal Wrangler publish command.

## Cloudflare Pages settings

| Setting | Value |
| --- | --- |
| Project | `speedslope-net` |
| Production branch | `main` |
| Build command | `python3 build_site.py && python3 validate_site.py` |
| Build output directory | `app` |
| Git automatic deployments | enabled |

Keep the existing `wrangler.toml` D1 binding for Pages Functions. D1 migrations and data changes are separate operations from ordinary site publishing.

## Local checks

```bash
python3 build_site.py
python3 validate_site.py
node check_game_availability.js changed-game-slug
```

## Rollback

Restore a known-good commit to `main`, or select the previous successful Pages deployment.
