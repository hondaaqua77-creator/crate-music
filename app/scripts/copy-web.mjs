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
let html = readFileSync(p, 'utf8').replace('<head>', '<head>\n<script>window.CRATE_NATIVE=true</script>');
// Production ads: the release build passes the AdMob ad unit ID (GitHub secret ADMOB_INTERSTITIAL_ID).
// Without it the app keeps Google's test ads, so test builds can never show real ads.
const adId = process.env.ADMOB_INTERSTITIAL_ID;
if (adId) {
  if (!/^ca-app-pub-\d+\/\d+$/.test(adId)) throw new Error('ADMOB_INTERSTITIAL_ID has the wrong form');
  const from = "const AD_CFG={test:true,interstitial:'ca-app-pub-3940256099942544/4411468910'";
  if (!html.includes(from)) throw new Error('AD_CFG not found in index.html');
  html = html.replace(from, `const AD_CFG={test:false,interstitial:'${adId}'`);
  const bannerId = process.env.ADMOB_BANNER_ID;
  if (bannerId) {
    if (!/^ca-app-pub-\d+\/\d+$/.test(bannerId)) throw new Error('ADMOB_BANNER_ID has the wrong form');
    const fromB = "banner:'ca-app-pub-3940256099942544/2934735716'";
    if (!html.includes(fromB)) throw new Error('banner id not found in index.html');
    html = html.replace(fromB, `banner:'${bannerId}'`);
  }
  console.log('using production AdMob ad unit');
}
writeFileSync(p, html);
console.log('copied web app to', out);
