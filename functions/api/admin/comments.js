import { isAdminRequest, json } from '../../_shared/comments.mjs';

const STATUSES = new Set(['pending', 'approved', 'rejected', 'hidden']);

export async function onRequestGet({ request, env }) {
  if (!isAdminRequest(request, env)) return json({ ok: false, error: 'Forbidden' }, 403);
  if (!env.COMMENTS_DB) return json({ ok: false, error: 'Comments are not configured yet.' }, 503);

  const url = new URL(request.url);
  const status = url.searchParams.get('status') || 'pending';
  if (!STATUSES.has(status)) return json({ ok: false, error: 'Unknown status.' }, 400);

  const rows = await env.COMMENTS_DB.prepare(
    `SELECT id, game_slug AS gameSlug, display_name AS displayName, email, body, status,
            created_at AS createdAt, moderated_at AS moderatedAt
     FROM comments
     WHERE status = ?
     ORDER BY created_at DESC
     LIMIT 100`
  ).bind(status).all();

  return json({ ok: true, comments: rows.results || [] });
}
