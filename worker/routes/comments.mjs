import { identityHash, json, validateCommentInput, validateSlug, verifyTurnstile } from '../comments.mjs';

export function commentsOptions() {
  return new Response(null, { status: 204 });
}

export async function getComments(request, env) {
  if (!env.COMMENTS_DB) return json({ ok: false, error: 'Comments are not configured yet.' }, 503);

  const url = new URL(request.url);
  const slug = validateSlug(url.searchParams.get('slug'));
  if (!slug.ok) return json({ ok: false, error: slug.error }, 400);

  const rows = await env.COMMENTS_DB.prepare(
    `SELECT id, display_name AS displayName, body, created_at AS createdAt
     FROM comments
     WHERE game_slug = ? AND status = 'approved'
     ORDER BY created_at DESC
     LIMIT 50`
  ).bind(slug.value).all();

  return json({ ok: true, comments: rows.results || [] });
}

export async function postComment(request, env) {
  if (!env.COMMENTS_DB) return json({ ok: false, error: 'Comments are not configured yet.' }, 503);

  let input;
  try {
    input = await request.json();
  } catch (_) {
    return json({ ok: false, error: 'Send a valid comment.' }, 400);
  }

  const checked = validateCommentInput(input);
  if (!checked.ok) return json({ ok: false, error: checked.error }, 400);

  const turnstile = await verifyTurnstile(input.turnstileToken || input['cf-turnstile-response'], request, env);
  if (!turnstile.ok) return json({ ok: false, error: turnstile.error }, 400);

  const now = new Date().toISOString();
  const since = new Date(Date.now() - 10 * 60 * 1000).toISOString();
  const ipHash = await identityHash(request, env);
  const recent = await env.COMMENTS_DB.prepare(
    `SELECT COUNT(*) AS count FROM comments WHERE ip_hash = ? AND created_at > ?`
  ).bind(ipHash, since).first();

  if (recent && Number(recent.count) >= 3) {
    return json({ ok: false, error: 'Too many comments. Try again later.' }, 429);
  }

  const comment = checked.value;
  await env.COMMENTS_DB.prepare(
    `INSERT INTO comments (game_slug, display_name, email, body, status, ip_hash, created_at)
     VALUES (?, ?, ?, ?, 'pending', ?, ?)`
  ).bind(comment.slug, comment.displayName, comment.email, comment.body, ipHash, now).run();

  return json({ ok: true, status: 'pending', message: 'Thanks. Your comment is waiting for review.' }, 202);
}
