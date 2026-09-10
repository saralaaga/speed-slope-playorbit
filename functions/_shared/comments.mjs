const MAX_NAME = 60;
const MAX_EMAIL = 254;
const MAX_BODY = 1000;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_RE = /(https?:\/\/|www\.|\b[a-z0-9][a-z0-9-]{1,}\.(?:com|net|org|io|xyz|top|club|online|site|info|biz|app|dev|co|cc|me|ru|cn|link|shop)\b)/i;
const SPAM_RE = /\b(casino|crypto|loan|viagra|betting|telegram|whatsapp|escort|porn|bonus|coupon code)\b/i;

function clean(value, max) {
  return String(value || '')
    .replace(/[\u0000-\u001f\u007f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

function fail(error) {
  return { ok: false, error };
}

export function validateSlug(slug) {
  const value = clean(slug, 90).toLowerCase();
  if (!value || value.length > 80 || !SLUG_RE.test(value)) return fail('Choose a valid game.');
  return { ok: true, value };
}

export function validateCommentInput(input) {
  const honeypot = clean(input.website || input.homepage || input.company, 200);
  if (honeypot) return fail('Spam check failed.');

  const slug = validateSlug(input.slug);
  if (!slug.ok) return slug;

  const displayName = clean(input.displayName || input.name, MAX_NAME) || 'Anonymous';
  if (URL_RE.test(displayName)) return fail('Names cannot contain links.');

  const email = clean(input.email, MAX_EMAIL).toLowerCase();
  if (email && !EMAIL_RE.test(email)) return fail('Enter a valid email address, or leave it blank.');

  const body = clean(input.body || input.comment, MAX_BODY);
  if (body.length < 3) return fail('Write a longer comment.');
  if (URL_RE.test(body)) return fail('Comments with links are not accepted.');
  if (SPAM_RE.test(body)) return fail('This comment looks like spam.');
  if (/(.)\1{8,}/.test(body)) return fail('This comment looks repetitive.');

  return {
    ok: true,
    value: {
      slug: slug.value,
      displayName,
      email: email || null,
      body,
    },
  };
}

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

export function clientIp(request) {
  return request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || '0.0.0.0';
}

export async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, '0')).join('');
}

export async function identityHash(request, env) {
  const salt = env.COMMENT_HASH_SALT || env.TURNSTILE_SECRET_KEY || 'dev-comment-salt';
  const ua = request.headers.get('user-agent') || '';
  return sha256Hex(`${salt}:${clientIp(request)}:${ua}`);
}

export function isAdminRequest(request, env) {
  const expectedToken = String(env.ADMIN_API_TOKEN || '').trim();
  const auth = request.headers.get('authorization') || '';
  const token = auth.match(/^Bearer\s+(.+)$/i)?.[1]?.trim() || '';
  if (expectedToken && token && token === expectedToken) return true;

  const accessJwt = request.headers.get('cf-access-jwt-assertion') || '';
  const host = new URL(request.url).hostname.toLowerCase();
  if (accessJwt && (host === 'speedslope.net' || host === 'www.speedslope.net')) return true;

  const email = (request.headers.get('cf-access-authenticated-user-email') || '').toLowerCase();
  const allowed = String(env.ADMIN_EMAILS || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  return Boolean(accessJwt && email && allowed.includes(email));
}

export async function verifyTurnstile(token, request, env) {
  if (!env.TURNSTILE_SECRET_KEY) return fail('Comment submissions are not configured yet.');
  if (!token) return fail('Complete the spam check.');

  const form = new FormData();
  form.append('secret', env.TURNSTILE_SECRET_KEY);
  form.append('response', token);
  form.append('remoteip', clientIp(request));

  const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: form,
  });
  if (!response.ok) return fail('Spam check failed.');
  const data = await response.json();
  return data.success ? { ok: true } : fail('Spam check failed.');
}
