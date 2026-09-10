# Comments Setup

The comments feature uses Cloudflare Pages Functions, D1, Turnstile, and Cloudflare Access.

## Bindings and Secrets

Create a D1 database and bind it to the Pages project as:

```text
COMMENTS_DB
```

Run the migration in `migrations/0001_comments.sql` against that database.

Set these environment variables/secrets on the Pages project:

```text
TURNSTILE_SECRET_KEY=<server secret from Cloudflare Turnstile>
COMMENT_HASH_SALT=<random long string>
ADMIN_EMAILS=you@example.com,other-admin@example.com
ADMIN_API_TOKEN=<random admin token>
```

Set the public Turnstile site key in `site_config.json`:

```json
"turnstile_site_key": "<public site key>"
```

Then rebuild:

```sh
python3 build_site.py
python3 validate_site.py
```

## Deploy

Cloudflare Pages deploys the generated `app/` directory and the `functions/` directory from the `main` branch through its native Git integration. Run the local build and validation commands before merging; do not deploy from a developer laptop with Wrangler.

## Moderation

Protect these paths with Cloudflare Access when the account token has Zero Trust permissions:

```text
/admin/*
/api/admin/*
```

Allow only the emails listed in `ADMIN_EMAILS`.

Cloudflare Access is configured with one app per hostname, covering both `/admin/*` and `/api/admin/*` on `speedslope.net` and `www.speedslope.net`. Keeping the page and API in the same Access app lets the browser reuse the same Access login session for moderation API calls. If Access is unavailable, `/admin/comments/` falls back to prompting for `ADMIN_API_TOKEN`. The token is stored in Bitwarden as `SPEEDSLOPE_ADMIN_TOKEN` and sent as a Bearer token to `/api/admin/*`.

Submitted comments are stored as `pending`. Public pages only show comments with `approved` status. Use `/admin/comments/` to approve, reject, or hide comments.

## Spam Rules

Server-side checks reject:

- missing or failed Turnstile validation
- filled honeypot fields
- invalid game slugs
- invalid optional email addresses
- URL-like text in names or comments
- common spam keywords
- highly repetitive comments
- more than 3 submissions from the same hashed IP/user-agent in 10 minutes
