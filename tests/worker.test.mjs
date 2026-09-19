import assert from 'node:assert/strict';

let worker;
try {
  ({ default: worker } = await import('../worker/index.mjs'));
} catch (error) {
  assert.fail(`Worker entrypoint is missing: ${error.message}`);
}

function database() {
  const queries = [];
  return {
    queries,
    prepare(sql) {
      queries.push(sql);
      const statement = {
        bind(...values) {
          statement.values = values;
          return statement;
        },
        all: async () => ({
          results: [{ id: 1, displayName: 'Carlos', body: 'Great game.', createdAt: '2026-01-01T00:00:00.000Z' }],
        }),
        first: async () => ({ count: 0 }),
        run: async () => ({ meta: { changes: 1 } }),
      };
      return statement;
    },
  };
}

{
  const response = await worker.fetch(
    new Request('https://speedslope.net/api/comments', { method: 'OPTIONS' }),
    { COMMENTS_DB: database() },
  );
  assert.equal(response.status, 204);
}

{
  const db = database();
  const response = await worker.fetch(
    new Request('https://speedslope.net/api/reports', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        slug: 'speed-slope',
        issue: 'not-loading',
        details: 'The frame stays blank after retry.',
      }),
    }),
    { COMMENTS_DB: db },
  );
  const data = await response.json();
  assert.equal(response.status, 202);
  assert.equal(data.ok, true);
  assert.ok(
    db.queries.some((query) => /INSERT INTO comments/.test(query) && /'hidden'/.test(query)),
    'expected report to be inserted into the hidden moderation queue'
  );
}

{
  const db = database();
  const response = await worker.fetch(
    new Request('https://speedslope.net/api/reports', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ slug: 'speed-slope', issue: 'not-a-real-issue' }),
    }),
    { COMMENTS_DB: db },
  );
  const data = await response.json();
  assert.equal(response.status, 400);
  assert.equal(data.ok, false);
  assert.equal(db.queries.length, 0);
}

{
  const db = database();
  const response = await worker.fetch(
    new Request('https://speedslope.net/api/comments?slug=neon-mini-golf'),
    { COMMENTS_DB: db },
  );
  const data = await response.json();
  assert.equal(response.status, 200);
  assert.equal(data.ok, true);
  assert.equal(data.comments[0].displayName, 'Carlos');
  assert.match(db.queries[0], /FROM comments/);
}

{
  const response = await worker.fetch(
    new Request('https://speedslope.net/api/comments', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ slug: 'neon-mini-golf', body: 'Nice physics.' }),
    }),
    {},
  );
  assert.equal(response.status, 503);
}

{
  const db = database();
  const response = await worker.fetch(
    new Request('https://speedslope.net/api/admin/comments/42', {
      method: 'PATCH',
      headers: {
        authorization: 'Bearer admin-token',
        'content-type': 'application/json',
      },
      body: JSON.stringify({ status: 'approved' }),
    }),
    { COMMENTS_DB: db, ADMIN_API_TOKEN: 'admin-token' },
  );
  const data = await response.json();
  assert.equal(response.status, 200);
  assert.equal(data.ok, true);
  assert.match(db.queries[0], /UPDATE comments/);
}

{
  const assets = {
    fetch: async (request) => new Response(`asset:${new URL(request.url).pathname}`, { status: 200 }),
  };
  const response = await worker.fetch(
    new Request('https://speedslope.net/games/arcade/'),
    { ASSETS: assets },
  );
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'asset:/games/arcade/');
}

{
  const response = await worker.fetch(
    new Request('https://speedslope.net/pool-duel/'),
    { ASSETS: { fetch: async () => new Response('asset', { status: 200 }) } },
  );
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://speedslope.net/');
}

{
  const response = await worker.fetch(
    new Request('https://speedslope.net/games/archery/'),
    { ASSETS: { fetch: async () => new Response('asset', { status: 200 }) } },
  );
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://speedslope.net/games/arcade/');
}
