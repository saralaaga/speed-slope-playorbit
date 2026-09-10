# Deployment

SpeedSlope is a generated Cloudflare Pages site with Pages Functions and a D1 comments binding.

## Flow

```text
local build/validate/game check
  -> push main
  -> GitHub Actions: build_site.py + validate_site.py
  -> wrangler pages deploy app
  -> Pages Functions and static files publish together
```

The `speedslope-net` Pages project was created by Direct Upload. Cloudflare cannot attach Git
integration to an existing Direct Upload project, so the repository deploys itself with the
`.github/workflows/deploy.yml` workflow instead. Pushing to `main` is still the only action
required, but the deploy is performed by GitHub Actions, not by Cloudflare's Git integration.

## Cloudflare Pages settings

| Setting | Value |
| --- | --- |
| Project | `speedslope-net` |
| Source | Direct Upload (Git integration not available) |
| Deployer | GitHub Actions, `.github/workflows/deploy.yml` |
| Production branch | `main` |
| Build command | `python3 build_site.py && python3 validate_site.py` (run inside the workflow) |
| Publish directory | `app` |

Repository secrets required by the workflow:

| Secret | Value |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | API token with the `Cloudflare Pages: Edit` permission |
| `CLOUDFLARE_ACCOUNT_ID` | `dad5acc42b3eb97b72f90f9c825339fe` |

Keep the existing `wrangler.toml` D1 binding for Pages Functions. D1 migrations and data changes are separate operations from ordinary site publishing.

## Local checks

```bash
python3 build_site.py
python3 validate_site.py
node check_game_availability.js changed-game-slug
```

## Rollback

Restore a known-good commit to `main`, or select the previous successful Pages deployment.
