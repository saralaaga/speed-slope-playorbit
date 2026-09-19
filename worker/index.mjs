import {
  commentsOptions,
  getComments,
  postComment,
} from './routes/comments.mjs';
import { postReport } from './routes/reports.mjs';
import {
  listAdminComments,
  updateAdminComment,
} from './routes/admin-comments.mjs';
import redirects from './redirects.json' with { type: 'json' };

const redirectsByPath = new Map(redirects.map((entry) => [entry.from, entry]));

function redirectFor(url) {
  const redirect = redirectsByPath.get(url.pathname);
  if (!redirect) return null;
  return Response.redirect(new URL(redirect.to, url), redirect.status);
}

async function handleApi(request, env) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (path === '/api/comments') {
    if (request.method === 'OPTIONS') return commentsOptions();
    if (request.method === 'GET') return getComments(request, env);
    if (request.method === 'POST') return postComment(request, env);
  }

  if (path === '/api/reports' && request.method === 'POST') {
    return postReport(request, env);
  }

  if (path === '/api/admin/comments' && request.method === 'GET') {
    return listAdminComments(request, env);
  }

  const commentUpdate = path.match(/^\/api\/admin\/comments\/(\d+)$/);
  if (commentUpdate && request.method === 'PATCH') {
    return updateAdminComment(request, env, { id: commentUpdate[1] });
  }

  return new Response(JSON.stringify({ ok: false, error: 'Not found' }), {
    status: 404,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) return handleApi(request, env);
    const redirect = redirectFor(url);
    if (redirect) return redirect;
    return env.ASSETS.fetch(request);
  },
};
