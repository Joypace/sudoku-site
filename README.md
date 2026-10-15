# Sudoku Let's Try website

Public static files only. No private App source, account credentials, puzzle packs, or player data.

## Hosting

Target: https://sudoku.joypace.com/ via GitHub Pages.
Publish `main`, repository root. `.nojekyll` preserves `.well-known` files.
`CNAME` contains `sudoku.joypace.com`.

DNS at the joypace.com provider:

| Type | Name | Target |
|---|---|---|
| CNAME | sudoku | joypace.github.io |

Replace the existing sudoku CNAME to pi.joypace.com, rather than adding a second record. Leave pi.joypace.com and all other records unchanged. Configure Pages custom domain before DNS cutover; wait for its certificate and enable HTTPS.

Enabling Pages or pushing after branch-based Pages is enabled may start GitHub's deployment workflow. Do not enable or request deployments without explicit client authorization under the current CI rule.

## Public routes

- `/app-ads.txt`: Google AdMob publisher declaration for both platforms.
- `/share/?p=…`: preserves the original query and fragment while forwarding to the existing read-only preview at pi.joypace.com. The compiled preview has NOT been migrated here. Keep the Pi site running.
- `/.well-known/apple-app-site-association`: public Apple association captured from the working share host before cutover. Signed application capabilities still govern native opening. Before DNS cutover, verify this extensionless file is actually served with Apple-compatible application/json Content-Type. GitHub Pages does not offer arbitrary response-header configuration; if its MIME type is incompatible, retain an appropriate front proxy/header rule or keep the existing host instead of claiming native opening is preserved. The current host returns 404 for Android assetlinks.json; Android verified HTTPS opening needs separately verified signing-certificate evidence. No certificate is invented here.

The existing preview uses nginx SSI for Safari's server-rendered Smart App Banner. Moving the full compiled preview requires qualifying a static-compatible banner and preserving the existing browser/app opening behavior, not copying the bootstrap HTML alone.

## AdMob verification

Set https://sudoku.joypace.com/ in the public App Store Marketing URL / Google Play developer website field. Once live, verify `/app-ads.txt` directly, then request AdMob's app-ads.txt check. TestFlight-only availability does not substitute for the public store listing.
