// House style check: no tabs, no src file over 150 lines.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

let failures = 0;
for (const name of readdirSync('src')) {
  if (!name.endsWith('.js')) continue;
  const text = readFileSync(join('src', name), 'utf8');
  if (text.includes('\t')) {
    console.error(`${name}: tabs are not allowed (use spaces)`);
    failures++;
  }
  const lines = text.split('\n').length;
  if (lines > 150) {
    console.error(`${name}: ${lines} lines (max 150) — split the module`);
    failures++;
  }
}
process.exit(failures > 0 ? 1 : 0);
