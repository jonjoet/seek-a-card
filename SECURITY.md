# Security model

Seek-a-Card is designed for children to use with an adult clue-giver. Its primary
security requirement is content integrity: the deployed app must not acquire or
display unreviewed material.

## Guarantees provided by the application design

The application has no feature that accepts a URL, uploads media, searches the
web, downloads a remote configuration, or requests generated content. Its only
card images are the files committed under `docs/assets/cards/` and referenced by
the generated `docs/cards.js` allowlist.

The page-level Content Security Policy denies all resources by default, denies
all network connections, and allows executable and visual resources only from
the same GitHub Pages origin. The service worker independently restricts its
cache and fetch handler to a generated list of exact same-origin asset URLs.

The app uses no third-party JavaScript packages, CDNs, analytics, advertising,
authentication, database, or server runtime. Local settings are parsed as data,
validated against the compiled card IDs, and never inserted as HTML.

SVG artwork is embedded through `<img>`, not inserted into the document. The
asset builder additionally rejects scripts, event handlers, embedded images,
foreign objects, external references, CSS URL references, and unexpected XML
elements. SHA-256 hashes of the reviewed files are committed in
`ASSET_HASHES.json`.

The builder trusts an already-downloaded illustration only when its bytes match
the hash recorded in `ASSET_HASHES.json`. A file that has been altered on disk
fails the build rather than being re-hashed as newly reviewed artwork, and a
hexcode with no recorded hash is always fetched from the pinned upstream
revision instead of being read from the working tree.

The two attribution links in the About dialog (openmoji.org and the CC BY-SA 4.0
deed) are the only external addresses named anywhere in the shipped files, and
the audit fails on any other. They are ordinary links: following one is a
deliberate navigation by the reader. The app itself still issues no requests off
its own origin, and `connect-src 'none'` continues to forbid it from doing so.

## Known limits of the deployed policy

The Content-Security-Policy is delivered in a `<meta>` tag, because GitHub Pages
serves static files and cannot set response headers. Two directives are
therefore unavailable:

- `frame-ancestors`, so the page can be embedded in a frame by another site.
  Nothing in the app is worth clickjacking: there is no sign-in, no stored
  credential, and no action that changes anything beyond the local device.
- `X-Content-Type-Options` and similar header-only protections.

Everything else in the policy is enforced by the browser exactly as written.

## Trust boundary

GitHub Pages publishes committed repository content. A person who can alter the
repository's deployed branch can alter the application and its content. Public
visibility does not grant write access: forks and unmerged pull requests cannot
change the published site.

Repository access and the owner's GitHub account are therefore part of the trust
boundary. Protect the account with a passkey or two-factor authentication, keep
the collaborator list minimal, and review every change before merging it into
`main`.

## Content-update policy

Artwork updates must be intentional and human-reviewed. Do not add live image
search or automatically merge an upstream artwork update. For any deck change:

1. Modify only the explicit card allowlist in `tools/build_assets.py`.
2. Keep the upstream revision pinned to a full commit SHA.
3. Run the builder and audit.
4. Inspect the complete rendered contact sheet.
5. Review the changed files and creator attributions before committing.

`tools/audit_site.py` runs on every push and pull request through
`.github/workflows/audit.yml`. It needs no network access, and it fails the
build if a card hash, the CSP, the service-worker allowlist, or the cache
revision does not match the committed files.

## Reporting a problem

Do not post sensitive family information in a public issue. If an inappropriate
or confusing card is found, disable it immediately in Parent settings on each
device, then remove the card from the source allowlist in the next repository
update.
