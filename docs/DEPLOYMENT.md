# Deployment

SpeedSlope is deployed as a Cloudflare Worker with Workers Static Assets and a
D1 comments binding. The Worker handles `/api/*` and legacy redirects; all other
requests are served from the generated `app/` directory.

## Short version

```bash
python3 build_site.py
node tests/worker.test.mjs
node tests/comments_filter.test.mjs
python3 validate_site.py
git push origin main
```

Pushing to `main` deploys. The GitHub Actions workflow rebuilds the site, runs
the Worker and filter tests, validates the generated output, and runs
`wrangler deploy`.

## Runtime shape

| Item | Value |
| --- | --- |
| Worker name | `speedslope-net` |
| Worker entry point | `worker/index.mjs` |
| Static asset directory | `app/` |
| Worker-first paths | all requests, so legacy redirects remain active |
| API paths | `/api/comments`, `/api/admin/comments/*` |
| D1 database | `speedslope-comments` |
| Production domains | `https://speedslope.net`, `https://www.speedslope.net` |
| Workflow | `.github/workflows/deploy.yml` |

The Worker processes redirects generated into `worker/redirects.json`. Pages
`_redirects` files are not used by Workers Static Assets, so removing that file
without this Worker map would turn removed game and category URLs into 404s.

## Cloudflare resources

The account ID remains:

```text
dad5acc42b3eb97b72f90f9c825339fe
```

`wrangler.toml` references the existing D1 database by ID. D1 migrations are
still a separate operational action and are not run during a normal content
deploy.

## Credentials

The GitHub repository secrets are:

| Secret | Use |
| --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID |
| `CLOUDFLARE_API_TOKEN` | account API token used by Wrangler |

The old Pages token is insufficient for Workers deployment. Create an account
API token with at least:

- **Account -> Workers Scripts -> Edit**
- **Account -> D1 -> Edit**
- custom-domain/route permissions if automating domain attachment

Store the value in the Infisical `speedslope` project first, then mirror it to
the GitHub secret:

```bash
gh secret set CLOUDFLARE_API_TOKEN -R saralaaga/speed-slope-playorbit
```

Do not commit or paste the token. Verify deployment permission by performing a
dry deploy or a real deploy; `/user/tokens/verify` is the wrong endpoint for
account-owned tokens.

## One-time Pages-to-Workers cutover

The apex and `www` domains cannot be attached to Pages and the Worker at the
same time. Use this order:

1. Update the repository token to the Workers/D1 permissions above.
2. Run `python3 build_site.py && python3 validate_site.py`.
3. Run `npx wrangler deploy` once to create/update the Worker and note its
   workers.dev URL.
4. Smoke-test static pages, `/api/comments?slug=neon-mini-golf`, and a removed
   game redirect on that preview URL.
5. In Cloudflare, remove `speedslope.net` and `www.speedslope.net` from the
   Pages project.
6. Add the same two custom domains to the `speedslope-net` Worker.
7. Verify both hostnames, comments API, admin moderation, and redirects.
8. After a soak period, disable or delete the old Pages project.

There is a brief DNS/routing cutover between steps 5 and 6. Perform it in a
maintenance window if comments and redirects need to remain continuously
available.

## Local checks

```bash
python3 build_site.py
python3 validate_site.py
node tests/worker.test.mjs
node tests/comments_filter.test.mjs
npx wrangler deploy --dry-run
```

For a local Worker/asset runtime:

```bash
python3 build_site.py
npx wrangler dev
```

The browser-based game availability gate is unchanged:

```bash
SITE_BASE_URL=http://127.0.0.1:8788 node check_game_availability.js changed-slug
SITE_BASE_URL=https://speedslope.net node check_game_availability.js changed-slug
```

## Verification after deploy

```bash
gh run list -R saralaaga/speed-slope-playorbit --limit 3
curl -s https://speedslope.net/games.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
curl -sI https://speedslope.net/pool-duel/ | head -1
```

The `games.json` entry count must match the build output. Workers deployments
are atomic, but browser/CDN caches can briefly retain the previous response.

## Rollback

For a bad Worker release, use Wrangler's version rollback from the deploy list
or re-run the last good GitHub Actions workflow. If a Worker-only rollback is
insufficient, redeploy a reverted commit on `main`; the repository remains the
source of truth.

Keep the old Pages project disabled, rather than deleting it immediately, until
the Worker deployment has passed production verification and the rollback
window.

## Manual deploy

Only use this for a hotfix when Actions is unavailable, and say so afterward:

```bash
python3 build_site.py && python3 validate_site.py
npx wrangler deploy
```
