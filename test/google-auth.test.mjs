import { test } from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPair, exportJWK, createLocalJWKSet, SignJWT } from 'jose';
import { createGoogleGate } from '../auth/google.mjs';

const canonical = 'https://sudoku.joypace.com';
const client = 'fixture.apps.googleusercontent.com';
const allowed = 'owner@example.test';
const approved = [allowed, 'qa@example.test', 'agent@example.test'];
const pair = await generateKeyPair('RS256');
const publicKey = await exportJWK(pair.publicKey);
const keys = createLocalJWKSet({ keys: [{ ...publicKey, kid: 'fixture', alg: 'RS256' }] });
const publicPaths = ['/', '/index.html', '/privacy/', '/app-ads.txt', '/share', '/share/', '/share/index', '/share/index.html',
  '/share/main.dart.js', '/.well-known/apple-app-site-association', '/.well-known/assetlinks.json'];
const gate = createGoogleGate(publicPaths, keys);

function setup(overrides = {}) {
  const calls = [];
  return { calls, env: { GOOGLE_WEB_CLIENT_ID: client, ALLOWED_EMAILS: JSON.stringify(approved),
    WEBAPP_SESSION_SECRET: 'fixture-session-key-which-is-longer-than-43-characters',
    ASSETS: { async fetch(request) {
      calls.push(request);
      if (new URL(request.url).pathname.startsWith('/share')) {
        return new Response('<meta content="app-argument=https://sudoku.joypace.com/share/">',
          { headers: { 'Content-Type': 'text/html' } });
      }
      return new Response(request.method === 'HEAD' ? null : 'fixture asset', {
        status: request.headers.has('Range') ? 206 : 200,
        headers: { 'Cache-Control': 'public, max-age=3600' },
      });
    } }, ...overrides } };
}

async function start(env) {
  const response = await gate.fetch(new Request(canonical + '/webapp/auth/login'), env);
  assert.equal(response.status, 200);
  const html = await response.text();
  return { nonce: /data-nonce="([a-f0-9]+)"/.exec(html)[1],
    transaction: response.headers.get('Set-Cookie').split(';')[0], html, response };
}

async function googleToken(nonce, overrides = {}, signingKey = pair.privateKey) {
  return new SignJWT({ iss: 'https://accounts.google.com', aud: client, sub: 'google-subject',
    email: allowed, email_verified: true, nonce,
    iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600,
    ...overrides }).setProtectedHeader({ alg: 'RS256', kid: 'fixture' }).sign(signingKey);
}

async function finish(env, flow, token, additions = {}) {
  return gate.fetch(new Request(canonical + '/webapp/auth/callback', { method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded',
      Cookie: flow.transaction + '; g_csrf_token=fixture-csrf', ...additions.headers },
    body: new URLSearchParams({ credential: token, g_csrf_token: 'fixture-csrf', ...additions.form }),
  }), env);
}

test('approved verified Google identity creates bounded HttpOnly session; every asset checks it', async () => {
  const { env, calls } = setup();
  const flow = await start(env);
  assert(flow.html.includes('data-ux_mode="redirect"'));
  assert(flow.html.includes('https://accounts.google.com/gsi/client'));
  assert.equal(flow.response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin');
  assert(flow.response.headers.get('Set-Cookie').includes('SameSite=None'));
  const response = await finish(env, flow, await googleToken(flow.nonce));
  assert.equal(response.status, 303);
  assert.equal(response.headers.get('Location'), canonical + '/webapp/');
  const cookie = response.headers.getSetCookie().find(c => c.startsWith('__Host-sudoku_webapp='));
  assert(cookie.includes('Secure; HttpOnly; SameSite=Lax; Max-Age=86400'));
  assert(response.headers.getSetCookie().some(c => c.startsWith('__Host-sudoku_google_nonce=;') && c.includes('Max-Age=0')));
  for (const path of ['/webapp/', '/webapp/index.html', '/webapp/main.dart.js',
    '/webapp/assets/assets/content/library/packs/2026-09-27.csv', '/webapp/canvaskit/canvaskit.wasm']) {
    for (const method of ['GET', 'HEAD']) {
      const result = await gate.fetch(new Request(canonical + path, { method,
        headers: { Cookie: cookie.split(';')[0], Range: 'bytes=0-10' } }), env);
      assert.equal(result.status, 206);
      assert.equal(result.headers.get('Cache-Control'), 'private, no-store');
    }
  }
  assert.equal(calls.length, 10);
  const removedUser = await gate.fetch(new Request(canonical + '/webapp/main.dart.js', {
    headers: { Cookie: cookie.split(';')[0] },
  }), { ...env, ALLOWED_EMAILS: JSON.stringify(approved.slice(1)) });
  assert.equal(removedUser.status, 401);
  assert.equal(calls.length, 10, 'Removed user must not reach ASSETS');
  for (const email of approved.slice(1)) {
    const otherFlow = await start(env);
    const signedIn = await finish(env, otherFlow, await googleToken(otherFlow.nonce, { email, sub: 'subject-' + email }));
    assert.equal(signedIn.status, 303);
    const otherCookie = signedIn.headers.getSetCookie().find(c => c.startsWith('__Host-sudoku_webapp='));
    const asset = await gate.fetch(new Request(canonical + '/webapp/main.dart.js', {
      headers: { Cookie: otherCookie.split(';')[0] },
    }), env);
    assert.equal(asset.status, 200);
  }
  assert.equal(calls.length, 12, 'All three configured accounts must pass callback and session checks');
  const logout = await gate.fetch(new Request(canonical + '/webapp/auth/logout', {
    method: 'POST', headers: { Origin: canonical, Cookie: cookie.split(';')[0] },
  }), env);
  assert.equal(logout.status, 303);
  assert(logout.headers.get('Set-Cookie').includes('__Host-sudoku_webapp=;'));
  assert(logout.headers.get('Set-Cookie').includes('Max-Age=0'));
});

test('untrusted identity claims and signatures never fetch private assets or issue sessions', async () => {
  const badPair = await generateKeyPair('RS256');
  for (const claims of [{ email: 'other@example.test' }, { email: 'owner+alias@example.test' },
    { email_verified: false }, { email_verified: 'true' }, { aud: 'native-client' },
    { iss: 'https://attacker.example' }, { exp: 1 }, { nonce: 'wrong' }, { sub: '' },
    { iat: 1 }, { azp: 'other-client' }]) {
    const { env, calls } = setup(); const flow = await start(env);
    const response = await finish(env, flow, await googleToken(flow.nonce, claims));
    assert.equal(response.status, 403, JSON.stringify(claims));
    assert(!response.headers.get('Set-Cookie').includes('__Host-sudoku_webapp='));
    assert.equal(calls.length, 0);
  }
  const { env } = setup(); const flow = await start(env);
  assert.equal((await finish(env, flow, await googleToken(flow.nonce, {}, badPair.privateKey))).status, 403);
});

test('CSRF, browser nonce, transaction signature, expiry and request shape fail closed', async () => {
  const { env, calls } = setup(); const flow = await start(env);
  const token = await googleToken(flow.nonce);
  for (const change of [{ form: { g_csrf_token: 'wrong' } },
    { headers: { Cookie: 'g_csrf_token=fixture-csrf' } },
    { headers: { Cookie: flow.transaction + 'tampered; g_csrf_token=fixture-csrf' } },
    { headers: { 'Content-Type': 'application/json' } }]) {
    assert.equal((await finish(env, flow, token, change)).status, 403);
  }
  const expired = await new SignJWT({ nonce: flow.nonce }).setProtectedHeader({ alg: 'HS256' })
    .setIssuer(canonical).setAudience('google-login').setIssuedAt(1).setExpirationTime(2)
    .sign(new TextEncoder().encode(env.WEBAPP_SESSION_SECRET));
  assert.equal((await finish(env, { ...flow, transaction: '__Host-sudoku_google_nonce=' + expired }, token)).status, 403);
  const oversized = new Request(canonical + '/webapp/auth/callback', { method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'x'.repeat(17000) });
  assert.equal((await gate.fetch(oversized, env)).status, 403);
  const repeated = new Request(canonical + '/webapp/auth/callback', { method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'credential=a&credential=b&g_csrf_token=c' });
  assert.equal((await gate.fetch(repeated, env)).status, 403);
  assert.equal(calls.length, 0);
});

test('missing, tampered, wrong-purpose, wrong-user and expired sessions cannot fetch private files', async () => {
  const { env, calls } = setup();
  const tokens = ['', 'forged'];
  for (const variant of [{ aud: 'google-login' }, { email: 'other@example.test' }, { exp: 1 }]) {
    tokens.push(await new SignJWT({ sub: 'google-subject', email: allowed,
      iss: canonical, aud: 'webapp-session', iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 3600, ...variant })
      .setProtectedHeader({ alg: 'HS256' }).sign(new TextEncoder().encode(env.WEBAPP_SESSION_SECRET)));
  }
  for (const token of tokens) {
    const response = await gate.fetch(new Request(canonical + '/webapp/main.dart.js', {
      headers: { Cookie: '__Host-sudoku_webapp=' + token, Range: 'bytes=0-10' }, method: 'HEAD',
    }), env);
    assert.equal(response.status, 401);
  }
  assert.equal(calls.length, 0);
});

test('all alternate origins, encoded aliases and unknown routes deny before static lookup', async () => {
  const { env, calls } = setup();
  for (const host of ['sudoku-joypace.pages.dev', 'build.sudoku-joypace.pages.dev', 'branch.sudoku-joypace.pages.dev']) {
    assert.equal((await gate.fetch(new Request('https://' + host + '/webapp/main.dart.js'), env)).status, 403);
    assert.equal((await gate.fetch(new Request('https://' + host + '/%77ebapp/main.dart.js'), env)).status, 400);
  }
  for (const path of ['/%77ebapp/main.dart.js', '/webapp%2fmain.dart.js', '/%2577ebapp/main.dart.js',
    '//webapp/main.dart.js', '/webapp/%252e%252e/main.dart.js', '/unknown/main.dart.js']) {
    assert([400, 404].includes((await gate.fetch(new Request(canonical + path), env)).status));
  }
  assert.equal(calls.length, 0);
});

test('public routes bypass authentication; dynamic share banner stays exact', async () => {
  const { env, calls } = setup({ GOOGLE_WEB_CLIENT_ID: undefined, WEBAPP_SESSION_SECRET: undefined });
  const sharePaths = ['/share', '/share/', '/share/index', '/share/index.html'];
  for (const path of publicPaths.filter(p => !sharePaths.includes(p))) {
    assert.equal((await gate.fetch(new Request(canonical + path), env)).status, 200);
  }
  for (const path of sharePaths) {
    const shared = await gate.fetch(new Request(canonical + path + '?p=123&v=2'), env);
    assert((await shared.text()).includes('app-argument=' + canonical + path + '?p=123&amp;v=2'));
    assert.equal(shared.headers.get('Cache-Control'), 'no-store');
  }
  assert.equal(calls.length, publicPaths.length);
});

test('configuration and allowed HTTP methods never expose private assets', async () => {
  for (const config of [{ GOOGLE_WEB_CLIENT_ID: undefined }, { WEBAPP_SESSION_SECRET: 'short' }, { ALLOWED_EMAILS: undefined },
    { ALLOWED_EMAILS: '[]' }, { ALLOWED_EMAILS: 'invalid' },
    { ALLOWED_EMAILS: JSON.stringify([allowed, 42]) },
    { ALLOWED_EMAILS: JSON.stringify([allowed, '*@example.test']) },
    { ALLOWED_EMAILS: JSON.stringify([allowed, allowed]) },
    { ALLOWED_EMAILS: '["example.test"]' },
    { ALLOWED_EMAILS: '[42]' }, { ALLOWED_EMAILS: '["bad"]' },
    { ALLOWED_EMAILS: '["Owner@example.test"]' }]) {
    const { env, calls } = setup(config);
    assert.equal((await gate.fetch(new Request(canonical + '/webapp/main.dart.js'), env)).status, 503);
    assert.equal(calls.length, 0);
  }
  const { env, calls } = setup();
  assert.equal((await gate.fetch(new Request(canonical + '/webapp/auth/callback'), env)).status, 405);
  assert.equal((await gate.fetch(new Request(canonical + '/webapp/main.dart.js', { method: 'POST' }), env)).status, 405);
  assert.equal((await gate.fetch(new Request(canonical + '/webapp/auth/logout', { method: 'POST',
    headers: { Origin: 'https://attacker.example' } }), env)).status, 403);
  assert.equal(calls.length, 0);
});
