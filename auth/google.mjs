import { SignJWT, jwtVerify, createRemoteJWKSet } from 'jose';
import { onRequest as share } from '../functions/share/index.js';

const origin = 'https://sudoku.joypace.com';
const sessionCookie = '__Host-sudoku_webapp';
const nonceCookie = '__Host-sudoku_google_nonce';
const googleKeys = createRemoteJWKSet(new URL('https://www.googleapis.com/oauth2/v3/certs'));
const encoder = new TextEncoder();

function allowedEmail(env) {
  const entries = JSON.parse(env.ALLOWED_EMAILS);
  if (!Array.isArray(entries) || entries.length !== 1 || typeof entries[0] !== 'string' ||
      !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(entries[0]) || entries[0] !== entries[0].toLowerCase()) {
    throw new Error('Invalid allowlist');
  }
  return entries[0];
}

function reply(body, status = 200, headers = {}) {
  return new Response(body, { status, headers: {
    'Cache-Control': 'private, no-store',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-Robots-Tag': 'noindex, nofollow',
    ...headers,
  } });
}

function cookie(name, value, age, sameSite = 'Lax') {
  return `${name}=${value}; Path=/; Secure; HttpOnly; SameSite=${sameSite}; Max-Age=${age}`;
}

function readCookie(request, name) {
  const values = (request.headers.get('Cookie') ?? '').split(';')
    .map(value => value.trim()).filter(value => value.startsWith(name + '='));
  return values.length === 1 ? values[0].slice(name.length + 1) : null;
}

function key(env) {
  if (typeof env.WEBAPP_SESSION_SECRET !== 'string' || env.WEBAPP_SESSION_SECRET.length < 43) {
    throw new Error('Missing session key');
  }
  return encoder.encode(env.WEBAPP_SESSION_SECRET);
}

async function sign(payload, env, purpose, duration) {
  return new SignJWT(payload).setProtectedHeader({ alg: 'HS256' }).setIssuer(origin)
    .setAudience(purpose).setIssuedAt().setExpirationTime(duration).sign(key(env));
}

async function verifyOwn(token, env, purpose, maxTokenAge) {
  if (!token || token.length > 4096) throw new Error('Missing token');
  const { payload } = await jwtVerify(token, key(env), {
    algorithms: ['HS256'], issuer: origin, audience: purpose,
    requiredClaims: ['exp', 'iat'], maxTokenAge,
  });
  return payload;
}

function randomNonce() {
  return Array.from(crypto.getRandomValues(new Uint8Array(32)), byte => byte.toString(16).padStart(2, '0')).join('');
}

async function sameValue(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || !a || !b || a.length > 4096 || b.length > 4096) return false;
  const [left, right] = await Promise.all([a, b].map(value => crypto.subtle.digest('SHA-256', encoder.encode(value))));
  const l = new Uint8Array(left), r = new Uint8Array(right);
  let mismatch = 0;
  for (let i = 0; i < l.length; i++) mismatch |= l[i] ^ r[i];
  return mismatch === 0;
}

async function boundedForm(request) {
  if (!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/x-www-form-urlencoded')) {
    throw new Error('Wrong content type');
  }
  const reader = request.body?.getReader();
  if (!reader) throw new Error('Missing body');
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > 16384) { await reader.cancel(); throw new Error('Body too large'); }
    chunks.push(value);
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  const form = new URLSearchParams(new TextDecoder().decode(body));
  for (const field of ['credential', 'g_csrf_token']) {
    if (form.getAll(field).length !== 1) throw new Error('Missing or repeated field');
  }
  return form;
}

async function login(env) {
  if (!/^[a-zA-Z0-9-]+\.apps\.googleusercontent\.com$/.test(env.GOOGLE_WEB_CLIENT_ID ?? '')) {
    return reply('Sign-in is not configured.', 503);
  }
  const nonce = randomNonce();
  const transaction = await sign({ nonce }, env, 'google-login', '10m');
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sign in — Sudoku Let's Try</title></head><body>
<h1>Sudoku Let's Try</h1><p>Sign in with your approved Google account.</p>
<script src="https://accounts.google.com/gsi/client" async></script>
<div id="g_id_onload" data-client_id="${env.GOOGLE_WEB_CLIENT_ID}" data-login_uri="${origin}/webapp/auth/callback" data-ux_mode="redirect" data-nonce="${nonce}" data-auto_prompt="false"></div>
<div class="g_id_signin" data-type="standard" data-text="signin_with"></div></body></html>`;
  // GIS redirects back with a cross-site POST; only this short-lived nonce cookie
  // uses SameSite=None. The application session remains SameSite=Lax.
  return reply(html, 200, { 'Content-Type': 'text/html; charset=utf-8',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Set-Cookie': cookie(nonceCookie, transaction, 600, 'None') });
}

async function callback(request, env, keys) {
  try {
    const form = await boundedForm(request);
    if (!await sameValue(readCookie(request, 'g_csrf_token'), form.get('g_csrf_token'))) throw new Error('CSRF');
    const transaction = await verifyOwn(readCookie(request, nonceCookie), env, 'google-login', '10m');
    const { payload } = await jwtVerify(form.get('credential'), keys, {
      algorithms: ['RS256'], issuer: ['https://accounts.google.com', 'accounts.google.com'],
      audience: env.GOOGLE_WEB_CLIENT_ID, requiredClaims: ['exp', 'iat', 'sub', 'email', 'email_verified', 'nonce'],
      maxTokenAge: '10m',
    });
    if (!await sameValue(payload.nonce, transaction.nonce) || payload.email !== allowedEmail(env) ||
        payload.email_verified !== true || typeof payload.sub !== 'string' || !payload.sub ||
        (payload.azp !== undefined && payload.azp !== env.GOOGLE_WEB_CLIENT_ID)) throw new Error('Not allowed');
    const session = await sign({ sub: payload.sub, email: payload.email }, env, 'webapp-session', '24h');
    const response = reply(null, 303, { Location: origin + '/webapp/' });
    response.headers.append('Set-Cookie', cookie(sessionCookie, session, 86400));
    response.headers.append('Set-Cookie', cookie(nonceCookie, '', 0, 'None'));
    return response;
  } catch {
    return reply('Sign-in was not accepted. Return to /webapp/auth/login to try again.', 403,
      { 'Set-Cookie': cookie(nonceCookie, '', 0, 'None') });
  }
}

export function createGoogleGate(publicPaths, keys = googleKeys) {
  const publicSet = new Set(publicPaths);
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      // All requests invoke this gate. Ambiguous paths never reach static lookup,
      // so provider decoding cannot turn a public-looking alias into a private file.
      if (/%|\\|\/\//.test(url.pathname)) return reply('Invalid path', 400);
      const isPrivate = url.pathname === '/webapp' || url.pathname.startsWith('/webapp/');
      if (!isPrivate) {
        if (!publicSet.has(url.pathname)) return reply('Not found', 404);
        if (!['GET', 'HEAD'].includes(request.method)) return reply('Method not allowed', 405);
        if (['/share', '/share/', '/share/index', '/share/index.html'].includes(url.pathname)) return share({ request, env });
        return env.ASSETS.fetch(request);
      }
      if (url.origin !== origin) return reply('Forbidden', 403);
      if (!/^[a-zA-Z0-9-]+\.apps\.googleusercontent\.com$/.test(env.GOOGLE_WEB_CLIENT_ID ?? '')) {
        return reply('Sign-in is not configured.', 503);
      }
      try { key(env); allowedEmail(env); } catch { return reply('Sign-in is not configured.', 503); }
      if (url.pathname === '/webapp/auth/callback') {
        return request.method === 'POST' ? callback(request, env, keys) : reply('Method not allowed', 405);
      }
      if (url.pathname === '/webapp/auth/login') {
        if (request.method !== 'GET') return reply('Method not allowed', 405);
        try { return await login(env); } catch { return reply('Sign-in is not configured.', 503); }
      }
      if (url.pathname === '/webapp/auth/logout') {
        if (request.method !== 'POST' || request.headers.get('Origin') !== origin) return reply('Forbidden', 403);
        return reply(null, 303, { Location: origin + '/webapp/auth/login', 'Set-Cookie': cookie(sessionCookie, '', 0) });
      }
      if (!['GET', 'HEAD'].includes(request.method)) return reply('Method not allowed', 405);
      try {
        const session = await verifyOwn(readCookie(request, sessionCookie), env, 'webapp-session', '24h');
        if (session.email !== allowedEmail(env) || typeof session.sub !== 'string' || !session.sub) throw new Error('Not allowed');
      } catch {
        if (['/webapp', '/webapp/', '/webapp/index.html'].includes(url.pathname)) {
          return reply(null, 302, { Location: origin + '/webapp/auth/login' });
        }
        return reply('Sign-in required', 401);
      }
      const asset = await env.ASSETS.fetch(request);
      const response = new Response(asset.body, asset);
      response.headers.set('Cache-Control', 'private, no-store');
      response.headers.set('X-Robots-Tag', 'noindex, nofollow');
      response.headers.set('Referrer-Policy', 'no-referrer');
      return response;
    },
  };
}
