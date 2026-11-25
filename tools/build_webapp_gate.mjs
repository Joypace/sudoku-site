import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { build } from 'esbuild';
import assert from 'node:assert/strict';
import {publicLessons} from './public_lessons.mjs';

// The public baseline and exact reviewed public additions determine which
// requests may reach static storage before authentication. App bundles and
// new server code cannot enter this allowlist.
const baseline = 'f4cbe27278189f9a917fde5c469adf0d10f5d5ef';
const root = path.resolve(import.meta.dirname, '..');
const output = path.resolve(process.argv[2] || path.join(root, '.auth-build'));
const files = process.env.SUDOKU_SITE_PUBLIC_BASELINE_FILES
  ? JSON.parse(await fs.readFile(process.env.SUDOKU_SITE_PUBLIC_BASELINE_FILES, 'utf8'))
  : execFileSync('git', ['ls-tree', '-r', '--name-only', '-z', baseline],
    { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean);
assert.equal(createHash('sha256').update(JSON.stringify(files)).digest('hex'), '36c2ded95e95874b07aa3731d695fbd776c2e8a6160e22f28cf5de74dbd3cf8b', 'Immutable public baseline file list changed');
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
// Public crawl metadata and the current read-only play badge images.
for (const file of ['robots.txt', 'sitemap.xml', 'googlebf6c56c3dfe44ecb.html', 'share/assets/assets/badges/ice.webp', 'share/assets/assets/badges/surge.webp']) {
  await fs.access(path.join(root, file));
  publicPaths.add('/' + file);
  exclusions.add('/' + file);
}
// Exact publisher notice pages and TikTok's URL-prefix ownership proof.
// Notice HTML remains on the Worker public allowlist to preserve the route budget.
for (const file of ['publisher/index.html', 'publisher/terms/index.html', 'publisher/privacy/index.html']) {
  await fs.access(path.join(root, file));
  const directory = '/' + file.slice(0, -10);
  publicPaths.add('/' + file);
  publicPaths.add('/' + file.slice(0, -5));
  publicPaths.add(directory);
  publicPaths.add(directory.slice(0, -1));
}
const publisherProof = '/publisher/tiktokZ6OBR3hRgbV5C1WqcyHvtLYmpsBDoNAE.txt';
await fs.access(path.join(root, publisherProof.slice(1)));
publicPaths.add(publisherProof);
exclusions.add(publisherProof);
// The complete reviewed learn subtree is public; no private release files may live there.
const lessons = await publicLessons(root);
if (lessons.length) {
  for (const file of lessons) {
    publicPaths.add('/' + file);
    if (file.endsWith('.html')) publicPaths.add('/' + file.slice(0, -5));
    if (file.endsWith('/index.html')) {
      const directory = '/' + file.slice(0, -10);
      publicPaths.add(directory); publicPaths.add(directory.slice(0, -1));
    }
  }
  exclusions.add('/learn/*');
}
// Pages normalizes HTML files to their exact extensionless alias.
publicPaths.add('/googlebf6c56c3dfe44ecb');
exclusions.add('/googlebf6c56c3dfe44ecb');
for (const route of exclusions) {
  if (route === '/learn/*') { assert(lessons.length > 0); continue; }
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
console.log(`Built gate: ${publicPaths.size} public paths, ${exclusions.size} static exemptions in ${output}`);
