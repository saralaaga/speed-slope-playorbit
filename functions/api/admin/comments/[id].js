import { isAdminRequest, json } from '../../../_shared/comments.mjs';

const STATUSES = new Set(['approved', 'rejected', 'hidden']);

export async function onRequestPatch({ request, env, params }) {
  if (!isAdminRequest(request, env)) return json({ ok: false, error: 'Forbidden' }, 403);
  if (!env.COMMENTS_DB) return json({ ok: false, error: 'Comments are not configured yet.' }, 503);

  const id = Number(params.id);
  if (!Number.isInteger(id) || id < 1) return json({ ok: false, error: 'Unknown comment.' }, 400);

  let input;
  try {
    input = await request.json();
  } catch (_) {
    return json({ ok: false, error: 'Send a valid moderation action.' }, 400);
  }

  const status = String(input.status || '').toLowerCase();
  if (!STATUSES.has(status)) return json({ ok: false, error: 'Unknown moderation status.' }, 400);

  const result = await env.COMMENTS_DB.prepare(
    `UPDATE comments SET status = ?, moderated_at = ? WHERE id = ?`
  ).bind(status, new Date().toISOString(), id).run();

  if (!result.meta || result.meta.changes === 0) return json({ ok: false, error: 'Comment not found.' }, 404);
  return json({ ok: true });
}
