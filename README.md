# Sudoku Let's Try website

Public static files only. No private App source, account credentials, puzzle packs, or player data.

## Hosting with Cloudflare Pages

Connect only `Joypace/sudoku-site` to Cloudflare Pages (not Workers).

| Setting | Value |
|---|---|
| Production branch | `main` |
| Framework preset | None |
| Build command | `exit 0` |
| Build output directory | `.` (repository root) |
| Root directory | Leave default |

The `_headers` file gives Apple's extensionless association JSON Content-Type. No Functions or secrets are needed. First verify the generated `*.pages.dev` URL, `/app-ads.txt` and the association's delivered Content-Type. The repository CNAME file belongs to the retained GitHub Pages setup; Cloudflare custom domains must be added in the Cloudflare dashboard.

Add `sudoku.joypace.com` in the Pages project's Custom domains **before** changing external DNS. Use the actual `*.pages.dev` hostname Cloudflare assigns; do not guess its name.

| DNS type | Name | Target |
|---|---|---|
| CNAME | sudoku | The assigned Cloudflare Pages hostname |

Replace the existing sudoku CNAME to pi.joypace.com. Leave pi.joypace.com, the blog and other DNS records unchanged. You do not need to transfer the joypace.com domain or change its nameservers for this subdomain setup.

GitHub Pages had one authorized deployment; GitHub Actions are disabled again. Connecting Cloudflare Git integration uses Cloudflare's own build service, not GitHub Actions. It normally deploys future main-branch pushes automatically; use Pages deployment controls if manual publication is desired.

## Public routes

- `/app-ads.txt`: Google AdMob publisher declaration for both platforms.
- `/share/?p=…`: preserves the original query and fragment while forwarding to the existing read-only preview at pi.joypace.com. The compiled preview has NOT been migrated here. Keep the Pi site running.
- `/.well-known/apple-app-site-association`: public Apple association captured from the working share host before cutover. Signed application capabilities still govern native opening. Before DNS cutover, verify this extensionless file is actually served with application/json Content-Type using the supplied Cloudflare header rule. The prior GitHub Pages deployment serves application/octet-stream and is not qualified for native opening. The current host returns 404 for Android assetlinks.json; Android verified HTTPS opening needs separately verified signing-certificate evidence. No certificate is invented here.

The existing preview uses nginx SSI for Safari's server-rendered Smart App Banner. Moving the full compiled preview requires qualifying a static-compatible banner and preserving the existing browser/app opening behavior, not copying the bootstrap HTML alone.

## AdMob verification

Set https://sudoku.joypace.com/ in the public App Store Marketing URL / Google Play developer website field. Once live, verify `/app-ads.txt` directly, then request AdMob's app-ads.txt check. TestFlight-only availability does not substitute for the public store listing.
