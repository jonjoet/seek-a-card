# Contributing

Content safety takes priority over deck size. Changes that introduce runtime
image search, user-supplied URLs, uploads, remote scripts, remote styles,
analytics, advertisements, dynamic configuration, or automatically accepted
artwork will not be accepted.

Before proposing a change:

1. Keep all production assets under `docs/` and all card images under
   `docs/assets/cards/`.
2. Add cards only through the explicit allowlist in `tools/build_assets.py`.
3. Keep the artwork source pinned to a full upstream commit SHA.
4. Run `python tools/build_assets.py` and `python tools/audit_site.py`. Re-run
   the builder after changing *any* precached file, not only the card list: it
   is what advances the service-worker cache revision, and a stale revision
   leaves already-installed devices on the previous build indefinitely.
5. Inspect the complete contact sheet produced by the audit.
6. Confirm that `THIRD_PARTY_NOTICES.md` identifies the source license and
   creator for every added image.

The application intentionally uses browser-native HTML, CSS, and JavaScript.
Adding a runtime package or build system requires a documented security reason.

The shipped files may not name any external address beyond the two attribution
links allowlisted in `tools/audit_site.py`, which exist to satisfy the CC BY-SA
4.0 terms for the bundled artwork. Adding another entry to that allowlist needs
the same scrutiny as any other content change.

Colours belong in the token block at the top of `docs/styles.css`. A literal
colour written further down the file will be wrong in one of the two themes.
The dark palette is written twice — once for the device preference and once for
the explicit override chosen in Appearance — and the audit fails if the two copies
diverge, so change both together.
