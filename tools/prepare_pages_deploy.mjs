import fs from 'node:fs/promises';
import path from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const [directory, assetReceipt, branch, output, sourceCommit] = process.argv.slice(2);
if (!directory || !assetReceipt || !branch || !output) throw new Error('Expected directory, asset receipt, branch, output');
const root = path.resolve(directory);
const assets = JSON.parse(await fs.readFile(assetReceipt, 'utf8'));
if (assets.summary.project !== 'sudoku-joypace' || assets.summary.missing !== 0) throw new Error('Assets not indexed for expected project');
const inner = 'SudokuWorker' + randomUUID(), outer = 'SudokuDeploy' + randomUUID();
const part = (boundary, name, value, type, filename) => '--' + boundary +
  '\r\nContent-Disposition: form-data; name="' + name + '"' +
  (filename ? '; filename="' + filename + '"' : '') + '\r\nContent-Type: ' + type + '\r\n\r\n' + value + '\r\n';
const worker = await fs.readFile(path.join(root, '_worker.js'), 'utf8');
const workerBundle = part(inner, 'metadata', JSON.stringify({ main_module: '_worker.js' }), 'application/json') +
  part(inner, '_worker.js', worker, 'application/javascript+module', '_worker.js') + '--' + inner + '--\r\n';
let body = part(outer, 'manifest', JSON.stringify(assets.manifest), 'text/plain') +
  part(outer, '_worker.bundle', workerBundle, 'multipart/form-data; boundary=' + inner, '_worker.bundle');
for (const [name, type] of [['_routes.json', 'application/json'], ['_headers', 'text/plain']]) {
  body += part(outer, name, await fs.readFile(path.join(root, name), 'utf8'), type, name);
}
body += part(outer, 'branch', branch, 'text/plain') +
  part(outer, 'commit_hash', sourceCommit || execFileSync('git', ['rev-parse', 'HEAD'], { cwd: new URL('../', import.meta.url), encoding: 'utf8' }).trim(), 'text/plain') +
  part(outer, 'commit_message', 'Reviewed Google gate with private deployment overlay', 'text/plain') +
  '--' + outer + '--\r\n';
await fs.writeFile(output, JSON.stringify({ contentType: 'multipart/form-data; boundary=' + outer,
  body, bodySha256: createHash('sha256').update(body).digest('hex'), branch,
  workerSha256: createHash('sha256').update(worker).digest('hex') }) + '\n');
console.log('Prepared multipart files, nested Worker module and explicit branch: ' + branch);
