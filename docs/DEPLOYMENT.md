# Deployment

SpeedSlope is a generated Cloudflare Pages site with Pages Functions and a D1 comments binding.
It publishes to `https://speedslope.net` (and `https://www.speedslope.net`).

## Short version

```bash
python3 build_site.py
python3 validate_site.py
node check_game_availability.js <changed-game-slugs>
git push origin main
```

Pushing to `main` is the deploy. Nothing else is required for a normal content change.

## Why the deploy runs in GitHub Actions

`speedslope-net` was created with Direct Upload. Cloudflare cannot attach Git integration to an
existing Direct Upload project, so Cloudflare never receives the repository and never sees a push.
The push-to-deploy pipeline therefore lives in GitHub Actions, which is Cloudflare's documented
continuous-integration path for Direct Upload projects.

The upside is that the build stays in this repository, so `build_site.py` and `validate_site.py`
run on the same inputs locally and in CI.

## Pipeline

```text
git push origin main
  -> .github/workflows/deploy.yml
  -> actions/checkout + actions/setup-python
  -> python3 build_site.py && python3 validate_site.py
  -> cloudflare/wrangler-action@v4
  -> wrangler pages deploy app --project-name=speedslope-net --branch=main
  -> static files + Pages Functions + D1 binding publish together
```

The workflow also accepts a manual run through `workflow_dispatch`.

## Fixed values

| Item | Value |
| --- | --- |
| Cloudflare account ID | `dad5acc42b3eb97b72f90f9c825339fe` |
| Pages project | `speedslope-net` |
| Publish directory | `app` |
| Production branch | `main` |
| Workflow | `.github/workflows/deploy.yml` |
| Site URL in `site_config.json` | `https://speedslope.net` |

## Credentials

The workflow needs two repository secrets:

| Secret | Value | State |
| --- | --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | `dad5acc42b3eb97b72f90f9c825339fe` | set |
| `CLOUDFLARE_API_TOKEN` | Cloudflare account API token with `Account > Cloudflare Pages > Edit` | **required** |

`CLOUDFLARE_API_TOKEN` is an account-owned token (`cfat_` prefix) and is stored in **Infisical**
under the `speedslope` project along with the project's other secrets. Mirror its value into the
GitHub repository secret; do not commit it and do not paste it into pull requests or issues.

To create or replace it:

1. Cloudflare dashboard -> **Manage Account** -> **Account API Tokens** -> **Create Token**
2. Permissions: **Account** -> **Cloudflare Pages** -> **Edit**. No other permission is needed.
3. Store the value in Infisical, then set the GitHub secret:

   ```bash
   gh secret set CLOUDFLARE_API_TOKEN -R saralaaga/speed-slope-playorbit
   ```

A token that verifies successfully but has no Pages permission is the most common failure. Check
permission rather than validity: `GET /accounts/<account_id>/pages/projects` must return
`success: true`, while `/user/tokens/verify` is the wrong endpoint for account-owned tokens and
always reports `Invalid API Token`.

## Local checks

```bash
python3 build_site.py                          # regenerates app/, reports games/categories/files
python3 validate_site.py                       # offline structural checks
node check_game_availability.js changed-slug   # browser check, see below
```

Run the availability check against a local build before pushing, and against production after the
deploy. It needs a served copy of `app/`:

```bash
python3 -m http.server 8123 --directory app &
SITE_BASE_URL=http://127.0.0.1:8123 node check_game_availability.js changed-slug
SITE_BASE_URL=https://speedslope.net node check_game_availability.js changed-slug
```

`AGENTS.md` lists the signals that disqualify an embed. Remove failing games via
`REMOVED_GAME_SLUGS` rather than shipping them.

## Verification after deploy

```bash
gh run list -R saralaaga/speed-slope-playorbit --limit 3   # wait for the run to succeed
curl -s https://speedslope.net/games.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```

The `games.json` entry count must match the build output. Cloudflare Pages serves the previous
deployment until the new one finishes, so a stale count right after a push is expected; compare
`app/games.json` in the commit against production once the workflow is green.

## Rollback

Re-run a previous successful workflow, or revert the offending commit on `main` and push. Both
routes rebuild from source, so the repository stays the source of truth. Selecting an older
deployment in the Cloudflare dashboard also works, but the next push will overwrite it.

## Manual deploy (escape hatch)

Only to get a hotfix out while the workflow is broken:

```bash
python3 build_site.py && python3 validate_site.py
npx wrangler pages deploy app --project-name=speedslope-net --branch=main
```

Say so when you do it, because production will then be ahead of the repository and the next push
will roll it back.

## Things that are not part of a normal deploy

- D1 migrations and the comments database. `wrangler.toml` carries the binding only; do not
  migrate the database as part of a content publish.
- `dist/`. It is a build artifact and is gitignored.
