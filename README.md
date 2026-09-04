# Seek-a-Card

Seek-a-Card is an installable, offline-friendly picture-card deck for a family
questions-and-guessing game. One player privately sees a card; the other players
have up to twenty yes-or-no questions to identify it.

The app contains 274 reviewed cards in six categories:

- Animals
- Food
- Things
- On the go
- Nature
- Shapes & colors

## Safety model

The published app is deliberately static and closed:

- All card artwork is stored in `docs/assets/cards/`.
- The app has no image search, remote API, upload feature, analytics, ads, user
  accounts, database, or server-side code.
- A restrictive Content Security Policy blocks network connections and permits
  images, scripts, and styles only from the app's own origin.
- The service worker caches only paths in the generated local asset allowlist,
  and precaches every one of them, so a device that has loaded the app once can
  play the whole deck with no network at all. Installation is all or nothing: a
  worker that could not store the complete allowlist never activates, so a
  partial download can never replace a complete offline deck.
- Card names are written with `textContent`; card data is never interpreted as
  HTML.
- Parent settings contain only known card IDs and are stored locally on the
  device.
- The asset builder is pinned to an exact OpenMoji revision and rejects active or
  externally referenced SVG content.

See [SECURITY.md](SECURITY.md) for the threat model and maintenance rules.

The app follows the device's light or dark appearance, or can be pinned to
either from **Appearance** in Parent settings; the choice is stored on that
device only. It is installable: the
manifest ships raster and vector icons, including an Apple touch icon for iOS
home screens. Inside a round, the system back gesture ends the round and returns
to deck setup rather than closing the app, and it never steps back onto a
revealed card.

## Checks

`.github/workflows/audit.yml` runs `tools/audit_site.py` on every push and pull
request. The audit needs no network access and fails closed.

Note that changing any precached file — `docs/app.js`, `docs/styles.css`,
`docs/index.html`, an icon, the service worker itself — means re-running
`python tools/build_assets.py` so the service-worker cache revision changes.
Without that, installed devices keep serving the previous build forever, because
the worker's own bytes never change and no update check is ever triggered. The
audit enforces this.

## GitHub Pages

Publish from the `main` branch and `/docs` directory:

1. Open **Settings → Pages**.
2. Under **Build and deployment**, select **Deploy from a branch**.
3. Choose branch **main**, directory **/docs**, and save.

The resulting site will be available at
`https://jonjoet.github.io/seek-a-card/`.

## Local development

Serve `docs/` from any local HTTP server. The production app has no runtime
dependencies and no build step.

To reproduce the reviewed artwork and generated card data:

```bash
python tools/build_assets.py
python tools/audit_site.py
```

Do not run the asset builder as an unattended scheduled job. Review changes to
the source allowlist, inspect every rendered asset, and run the audit before
committing an update.

## Licenses

The application code is available under the [MIT License](LICENSE).

Card illustrations are from OpenMoji and are separately licensed under CC
BY-SA 4.0. They are not covered by the repository's MIT License. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the pinned source revision
and per-file creator attribution.
