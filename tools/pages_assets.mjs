import fs from 'node:fs/promises';
import path from 'node:path';
import { createECDH, createDecipheriv, createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

import { hash } from 'blake3-wasm';
const root = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const upload = process.argv.includes('--upload');
const envelope = JSON.parse(await fs.readFile(new URL('../../private/pages-upload-envelope.json', import.meta.url), 'utf8'));
if (envelope.project !== 'sudoku-joypace') throw new Error('Wrong project token');
const local = createECDH('prime256v1');
local.setPrivateKey(await fs.readFile(new URL('../../private/pages-upload-transport.key', import.meta.url)));
const key = local.computeSecret(Buffer.from(envelope.sender, 'base64'));
const encrypted = Buffer.from(envelope.ciphertext, 'base64');
const decipher = createDecipheriv('aes-256-gcm', key, Buffer.from(envelope.iv, 'base64'));
decipher.setAuthTag(encrypted.subarray(-16));
const token = Buffer.concat([decipher.update(encrypted.subarray(0, -16)), decipher.final()]).toString();
const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
if (claims.exp <= Date.now() / 1000 + 120) throw new Error('Project upload token needs renewal');

const metadata = JSON.parse(execFileSync('python3', ['-c',
  'import json,mimetypes,sys;from pathlib import Path;r=Path(sys.argv[1]);print(json.dumps({str(p.relative_to(r)):mimetypes.guess_type(str(p))[0] or "application/octet-stream" for p in r.rglob("*") if p.is_file()}))', root],
  { encoding: 'utf8' }));
const files = [];
for (const [name, contentType] of Object.entries(metadata)) {
  if (['_worker.js', '_routes.json', '_headers', '_redirects'].includes(name) ||
      name.startsWith('functions/') || name.split('/').some(n => ['.git', 'node_modules', '.wrangler', '.DS_Store'].includes(n))) continue;
  const file = path.join(root, name), data = await fs.readFile(file);
  if (data.byteLength > 25 * 1024 * 1024) throw new Error('Asset exceeds Pages size limit: ' + name);
  files.push({ name, path: file, bytes: data.byteLength,
    hash: hash(data.toString('base64') + path.extname(name).slice(1)).toString('hex').slice(0, 32),
    sha256: createHash('sha256').update(data).digest('hex'), contentType });
}
if (files.length > (claims.max_file_count_allowed ?? 20000)) throw new Error('Asset count exceeds project quota');

async function api(endpoint, body) {
  const response = await fetch('https://api.cloudflare.com/client/v4/pages/assets/' + endpoint, {
    method: 'POST', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok || !result.success) throw new Error(endpoint + ' failed HTTP ' + response.status +
    ', codes ' + (result.errors ?? []).map(e => e.code).join(','));
  return result.result;
}

const hashes = [...new Set(files.map(f => f.hash))];
if (process.argv.includes('--register-existing')) await api('upsert-hashes', { hashes });
const missing = new Set(await api('check-missing', { hashes }));
const selected = [...new Map(files.filter(f => missing.has(f.hash)).map(f => [f.hash, f])).values()];
const summary = { project: 'sudoku-joypace', directory: root, files: files.length,
  reused: files.filter(f => !missing.has(f.hash)).length, missing: selected.length,
  missingBytes: selected.reduce((n, f) => n + f.bytes, 0), uploaded: false };
const manifest = Object.fromEntries(files.map(f => ['/' + f.name, f.hash]));
await fs.writeFile(output, JSON.stringify({ summary, manifest, files }, null, 2) + '\n');
console.log(JSON.stringify(summary));
if (upload) {
  let batch = [], size = 0, sent = 0;
  async function flush() {
    if (!batch.length) return;
    await api('upload', await Promise.all(batch.map(async f => ({ key: f.hash,
      value: (await fs.readFile(f.path)).toString('base64'), base64: true,
      metadata: { contentType: f.contentType } }))));
    sent += batch.length;
    console.log(JSON.stringify({ uploadedAssets: sent, totalMissing: selected.length }));
    batch = []; size = 0;
  }
  for (const file of selected) {
    if (size + file.bytes > 20 * 1024 * 1024) await flush();
    batch.push(file); size += file.bytes;
  }
  await flush();
  await api('upsert-hashes', { hashes });
  const remaining = await api('check-missing', { hashes });
  if (remaining.length) throw new Error('Asset index incomplete; check before retry');
  summary.initialMissing = summary.missing;
  summary.missing = 0;
  summary.missingBytes = 0;
  summary.uploaded = true;
  await fs.writeFile(output, JSON.stringify({ summary, manifest, files }, null, 2) + '\n');
  console.log('Assets verified present. No deployment created by this tool.');
}
