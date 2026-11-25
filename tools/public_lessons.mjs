import {execFileSync} from 'node:child_process';
import path from 'node:path';
// One build-time contract owns the public namespace, input proofs and SVG safety.
export async function publicLessons(root) {
  return JSON.parse(execFileSync('python3', [path.join(import.meta.dirname, 'validate_lessons.py'), root], {encoding:'utf8'}));
}
