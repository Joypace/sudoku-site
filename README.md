# Sudoku Let's Try website

Public static files only. No private App source, account credentials, puzzle packs, or player data.

## Private webapp authentication

`auth/google.mjs` verifies Google Identity Services redirect-POST credentials and
allows only verified accounts in the server-side `ALLOWED_EMAILS` binding.
It checks Google's signature,
issuer, web-client audience, expiry and nonce, plus Google's double-submit CSRF
token. Successful sign-in creates a Secure, HttpOnly session bounded to 24 hours.
The dedicated Google project is `sudoku-web-sign-in`; native clients are separate.

`node tools/build_webapp_gate.mjs` builds the Pages advanced-mode Worker and its
invocation routes into ignored `.auth-build/`. Its public allowlist comes from the
immutable public site baseline plus reviewed metadata/image paths and the validated public lesson catalogue; exact static exemptions preserve the homepage,
policy, association files and public assets outside the Functions quota. Share
HTML remains dynamic. Every private or unknown route outside the deliberately public learning subtree reaches the gate, ambiguous
paths are rejected, and alternative origins cannot serve `/webapp` assets.
The owning scenarios run with `npm run test:auth`.

The deployment overlay requires `GOOGLE_WEB_CLIENT_ID`, the secret binding
`ALLOWED_EMAILS` containing a nonempty JSON array of unique exact lowercase email
addresses (no domains or wildcards), and a random server-only
`WEBAPP_SESSION_SECRET` of at least 43 characters. Both deployment environments
must fail closed before a protected static payload is uploaded. Local tests do
not prove live routing, cache behavior or Google's browser flow; a harmless
provider probe must qualify those first. Free Functions exhaustion can interrupt
the webapp and dynamic sharing, while exact excluded public assets remain static.

Playable App files and puzzle packs stay in a private deployment overlay outside
this public repository. They must never enter Git, even when HTTP access is gated.

The maintained manual-release helpers are `tools/prepare_pages_token_request.mjs`,
`tools/pages_assets.mjs`, and `tools/prepare_pages_deploy.mjs`. Project upload
tokens stay encrypted or in memory outside this repository. The asset helper
uploads content only; the deployment helper prepares the multipart request, with
real File parts and nested Worker metadata. `python3 test/pages_multipart_test.py`
pins the upload-format defect that otherwise produces a static-only deployment.
The Pages project's automatic production Git deployments are disabled for composed
private releases; a source-only deployment cannot carry the private runtime.

## Homepage preview

Serve this directory locally to review the homepage (for example,
`python3 -m http.server 8090 --bind 127.0.0.1`). It uses `home.css`, `home.js`
and optimized WebP App screenshots in `home-assets/`; no remote font or build
step is required to view it. Clicking a screenshot opens its full-size view.
Tip demonstrations are standalone animated SVGs exported by the App's formal
`docs/ued/tips/bake.py` tool. The exporter records the current App tip's real
painters and timing offline; the website uses native SVG playback only. It
ships no Flutter runtime, puzzle model or replacement gesture interpreter.
Animations start when visible, repeat after a 1.5-second pause, and stop offscreen.
Reduced-motion preferences disable autoplay.
Run `node test/homepage.mjs http://127.0.0.1:8090/` for local playback checks.
Website publication remains separate from App releases.

The homepage’s App Store button uses `/app-store`. The Worker redirects Canadian
IP locations to the Canada storefront and all other or unknown locations to the
USA storefront, using Cloudflare’s request country. Redirects are not cached;
there is no external location lookup. Apple Account region still controls purchase availability.
The download lockup pairs the app icon with Apple’s unchanged official black
[App Store badge](https://developer.apple.com/assets/elements/badges/download-on-the-app-store.svg),
embedded as an image to avoid a remote request. Its 48px height has 12px clear space.


## Technique lessons

`learn/manifest.json` is the public catalogue, ordered from simple to advanced.
Keep new lessons in the appropriate learning position. Several lessons may share a
publication date; completed lessons can be published as ready. Each page has3–5 original practice examples, a real App-exported
SVG animation and a native puzzle-share link for every example. The animation's
starting givens must match the link; no hidden note edits may precede playback.

The private Ops authoring/export/scheduling workflow lives outside this public
repository at `workshops/ops/technique-pages`. It uses the existing App tutorial
player and painters. No App source or puzzle packs are copied into the site.
The page provides complete written reasoning and explicit play/pause/replay/seek
controls; animations start paused and stop offscreen or when the tab hides.

`tools/validate_lessons.py` owns the public subtree contract, including safe file
names, original-grid share decoding, unique solutions, technique proof rules,
App scenario provenance and the narrow native-SVG format. Unsupported proof rules
fail before publication; new techniques add their own owning validator/test.
The gate builder adds only the literal `/learn/*` static exclusion and exact
known paths/aliases, keeping the combined Pages route budget bounded. Run
`python3 test/lessons_test.py` and the isolated browser test
`node test/lessons_browser.mjs LOCAL_LESSON_URL QA_OUTPUT` with the existing checks.

## Public search metadata

The homepage, Help and Privacy pages declare their canonical HTTPS URLs in the
sitemap. `robots.txt` announces the sitemap and excludes the private webapp from
crawling; authentication remains the access control.

Help's readable HTML comes from the same App tip catalogue as its animations.
After a catalogue update, run `node tools/render_help.mjs`; the existing asset
test checks that the generated HTML stays current. `help.js` adds lazy playback,
single-expanded tips and direct lesson links to that HTML.

Search Console verification and indexing are provider state, not a consequence
of publishing metadata. No ratings, reviews or search-result eligibility are claimed.

## Hosting with Cloudflare Pages

The existing Pages project is `sudoku-joypace`, serving `sudoku.joypace.com`.
The public repository is `Joypace/sudoku-site`, production branch `main`.
Automatic production Git deployments and GitHub Actions remain disabled.

Publish through the composed-private-release helpers described in
[Private webapp authentication](#private-webapp-authentication). A public-source
push alone cannot carry the protected runtime and must not replace a complete
release. Keep existing DNS, custom domains, sign-in bindings and preview/production
controls unchanged unless the user requests a separate hosting change.

## Public routes

- `/app-ads.txt`: Google AdMob publisher declaration for both platforms.
- `/privacy/`: app privacy policy for individual developer Li Zhang, contact sudoku@joypace.com.
- `/share/?p=…`: serves the existing compiled read-only preview and its local renderer/font resources on this host. There is no Pi redirect. Existing pi.joypace.com links continue working independently.
- `/.well-known/apple-app-site-association`: public Apple association captured from the working share host before cutover. Signed application capabilities still govern native opening. Before DNS cutover, verify this extensionless file is actually served with application/json Content-Type using the supplied Cloudflare header rule. The prior GitHub Pages deployment serves application/octet-stream and is not qualified for native opening. Android `assetlinks.json` names the actual Play app-signing certificate, checked against the public certificate in `test/fixtures/play-signing.der`. Deploy that association on the sole `sudoku.joypace.com` share host; the upload key is not the Play distribution identity.

The read-only preview uses the qualified App layout (source 4885cf4e95e6720b9e9ab4cf4768d6e32247886a; main.dart.js SHA256 4d58ef01610f929dd3b211598bc4e2239e792d1379f3f44aecf2c6425134fa02). Its runtime licences are included. The HTML banner is generated by functions/share/index.js with escaped current URL and no-store caching, replacing nginx SSI. The generated routes keep the approved public image/JS/Wasm/font requests static. The preview creates no profile/session, exports no gameplay controller and preserves its existing read-only behavior.

## AdMob verification

Set https://sudoku.joypace.com/ in the public App Store Marketing URL / Google Play developer website field. Once live, verify `/app-ads.txt` directly, then request AdMob's app-ads.txt check. TestFlight-only availability does not substitute for the public store listing.

## Review the site after an App update

The App release owner supplies the verified revision and public feature changes;
the website owner reviews the affected sections. For each release, run this local,
read-only check with the exact
candidate revision available in the App checkout:

```sh
python3 tools/check_app_update.py --app /path/to/sudoku_app --ref VERIFIED_APP_SHA
```

It compares against `app-source.json`, lists sections needing review, and exits
2 when a review is needed. It does not fetch, build, publish or start Actions.
Review the relevant App/content diff before deciding whether the page needs a
change; unrelated internal changes do not require a new animation. SVG metadata
keeps the revision actually captured; `app-source.json` records the revision
reviewed.

Regenerate affected tips with the App's formal `docs/ued/tips/bake.py
--export-svg` command, or use `--export-catalog` for the complete Help list.
`--export-screens` records the actual Journey/Library/sharing widgets offline;
these screen tours retain 2x image captures inside SVG, while gesture tips retain
vector grids, text and marks (shader/sprite layers use recorded image textures).
Do not draw a second version of the App UI or run Flutter in the homepage.

Review the local page at phone, tablet and desktop widths, then run
`node test/homepage.mjs`, `python3 test/assets_test.py`, and
`python3 test/app_update_test.py`. Check captions,
section claims, gesture timing, scrolling, visibility/looping, and Help's
single-expanded-tip behavior. After review, record the exact reviewed App and
content refs in `app-source.json`. Keep publication separate from an App release:
use the existing website owner/deployment path only when publication is authorized.
Also compare the release’s SDK/platform and App-opening configuration when those
change. No Actions are started by this process.
