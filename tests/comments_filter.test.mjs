import assert from 'node:assert/strict';
import { isAdminRequest, validateCommentInput } from '../worker/comments.mjs';

function valid(overrides = {}) {
  return {
    slug: 'neon-mini-golf',
    displayName: '',
    email: '',
    body: 'Fun course. The bank shots feel fair.',
    website: '',
    ...overrides,
  };
}

{
  const result = validateCommentInput(valid());
  assert.equal(result.ok, true);
  assert.equal(result.value.displayName, 'Anonymous');
  assert.equal(result.value.email, null);
}

{
  const result = validateCommentInput(valid({ displayName: 'Carlos', email: 'carlos@example.com' }));
  assert.equal(result.ok, true);
  assert.equal(result.value.displayName, 'Carlos');
  assert.equal(result.value.email, 'carlos@example.com');
}

{
  const result = validateCommentInput(valid({ email: 'not-an-email' }));
  assert.equal(result.ok, false);
  assert.match(result.error, /email/i);
}

{
  const result = validateCommentInput(valid({ body: 'Play here https://spam.example now' }));
  assert.equal(result.ok, false);
  assert.match(result.error, /links/i);
}

{
  const result = validateCommentInput(valid({ body: 'Visit www.spam.example for coins' }));
  assert.equal(result.ok, false);
  assert.match(result.error, /links/i);
}

{
  const result = validateCommentInput(valid({ website: 'filled by bot' }));
  assert.equal(result.ok, false);
  assert.match(result.error, /spam/i);
}

{
  const result = validateCommentInput(valid({ slug: '../admin' }));
  assert.equal(result.ok, false);
  assert.match(result.error, /game/i);
}

{
  const request = new Request('https://speedslope.net/api/admin/comments', {
    headers: { 'cf-access-authenticated-user-email': 'admin@example.com' },
  });
  assert.equal(isAdminRequest(request, { ADMIN_EMAILS: 'admin@example.com', ADMIN_API_TOKEN: 'secret-token' }), false);
}

{
  const request = new Request('https://speedslope.net/api/admin/comments', {
    headers: { authorization: 'Bearer secret-token' },
  });
  assert.equal(isAdminRequest(request, { ADMIN_API_TOKEN: 'secret-token' }), true);
}

{
  const request = new Request('https://speedslope.net/api/admin/comments', {
    headers: { 'cf-access-jwt-assertion': 'access-jwt' },
  });
  assert.equal(isAdminRequest(request, {}), true);
}

{
  const request = new Request('https://speedslope-net.example.workers.dev/api/admin/comments', {
    headers: { 'cf-access-jwt-assertion': 'access-jwt' },
  });
  assert.equal(isAdminRequest(request, {}), false);
}
