import { identityHash, json, validateReportInput } from '../comments.mjs';

export async function postReport(request, env) {
  if (!env.COMMENTS_DB) return json({ ok: false, error: 'Reports are not configured yet.' }, 503);

  let input;
  try {
    input = await request.json();
  } catch (_) {
    return json({ ok: false, error: 'Send a valid report.' }, 400);
  }

  const checked = validateReportInput(input);
  if (!checked.ok) return json({ ok: false, error: checked.error }, 400);

  const now = new Date().toISOString();
  const since = new Date(Date.now() - 10 * 60 * 1000).toISOString();
  const ipHash = await identityHash(request, env);
  const recent = await env.COMMENTS_DB.prepare(
    `SELECT COUNT(*) AS count FROM comments WHERE ip_hash = ? AND created_at > ?`
  ).bind(ipHash, since).first();

  if (recent && Number(recent.count) >= 3) {
    return json({ ok: false, error: 'Too many reports. Try again later.' }, 429);
  }

  const report = checked.value;
  await env.COMMENTS_DB.prepare(
    `INSERT INTO comments (game_slug, display_name, email, body, status, ip_hash, created_at)
     VALUES (?, 'Broken game report', NULL, ?, 'hidden', ?, ?)`
  ).bind(report.slug, report.body, ipHash, now).run();

  return json({ ok: true, message: 'Thanks. We will check this game.' }, 202);
}
