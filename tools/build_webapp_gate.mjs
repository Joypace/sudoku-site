import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { build } from 'esbuild';
import assert from 'node:assert/strict';

// The public baseline determines which requests may reach static storage before
// authentication. App bundles and new server code cannot enter this allowlist.
const baseline = 'f4cbe27278189f9a917fde5c469adf0d10f5d5ef';
const root = path.resolve(import.meta.dirname, '..');
const output = path.resolve(process.argv[2] || path.join(root, '.auth-build'));
const files = execFileSync('git', ['ls-tree', '-r', '--name-only', '-z', baseline],
  { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean);
const publicPaths = new Set();
const exclusions = new Set(['/', '/privacy', '/privacy/', '/help', '/help/']);
const shareEntries = new Set(['/share', '/share/', '/share/index', '/share/index.html']);
for (const file of files) {
  if (file.startsWith('functions/') || file.startsWith('_') || file.startsWith('.git')) continue;
  publicPaths.add('/' + file);
  if (!/^(README\.md|CNAME|\.nojekyll|test\/|tools\/)/.test(file) && !shareEntries.has('/' + file)) {
    exclusions.add('/' + file);
  }
  if (file.endsWith('.html')) publicPaths.add('/' + file.slice(0, -5));
  if (file === 'index.html' || file.endsWith('/index.html')) {
    const directory = '/' + file.slice(0, -10);
    publicPaths.add(directory);
    if (directory !== '/') publicPaths.add(directory.slice(0, -1));
  }
}
for (const route of exclusions) {
  assert(publicPaths.has(route), 'Exclusion outside immutable public baseline');
  assert(!/[\*%\\?#]|\/\//.test(route) && !/(^|\/)\.{1,2}(\/|$)/.test(route), 'Ambiguous exclusion');
  assert(route !== '/webapp' && !route.startsWith('/webapp/') && !shareEntries.has(route), 'Protected exclusion');
}
assert(exclusions.size <= 99, 'Pages invocation route budget exceeded');
await fs.mkdir(output, { recursive: true });
await build({ stdin: { contents: `import {createGoogleGate} from './auth/google.mjs';\nexport default createGoogleGate(${JSON.stringify([...publicPaths].sort())});`,
  resolveDir: root, sourcefile: 'webapp-worker-entry.mjs' },
  bundle: true, format: 'esm', platform: 'browser', target: 'es2022',
  outfile: path.join(output, '_worker.js') });
await fs.writeFile(path.join(output, '_routes.json'), JSON.stringify({ version: 1, include: ['/*'], exclude: [...exclusions].sort() }) + '\n');
await fs.writeFile(path.join(output, 'public-paths.json'), JSON.stringify([...publicPaths].sort(), null, 2) + '\n');
console.log(`Built gate: ${publicPaths.size} public baseline paths, ${exclusions.size} exact static exemptions in ${output}`);
