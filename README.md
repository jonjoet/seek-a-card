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
- The service worker caches only paths in the generated local asset allowlist.
- Card names are written with `textContent`; card data is never interpreted as
  HTML.
- Parent settings contain only known card IDs and are stored locally on the
  device.
- The asset builder is pinned to an exact OpenMoji revision and rejects active or
  externally referenced SVG content.

See [SECURITY.md](SECURITY.md) for the threat model and maintenance rules.

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
