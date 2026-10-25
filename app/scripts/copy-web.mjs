// Copies the web app (repo root) into app/www for the iOS build.
// The web version on GitHub Pages stays the source of truth; nothing here edits it.
import { cpSync, rmSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..');
const out = join(here, '..', 'www');
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
for (const f of ['index.html', 'manifest.webmanifest']) cpSync(join(root, f), join(out, f));
for (const d of ['icons', 'vendor']) cpSync(join(root, d), join(out, d), { recursive: true });
// Mark the build as the native app (the page reads window.CRATE_NATIVE).
const p = join(out, 'index.html');
writeFileSync(p, readFileSync(p, 'utf8').replace('<head>', '<head>\n<script>window.CRATE_NATIVE=true</script>'));
console.log('copied web app to', out);
