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
4. Run `python tools/build_assets.py` and `python tools/audit_site.py`.
5. Inspect the complete contact sheet produced by the audit.
6. Confirm that `THIRD_PARTY_NOTICES.md` identifies the source license and
   creator for every added image.

The application intentionally uses browser-native HTML, CSS, and JavaScript.
Adding a runtime package or build system requires a documented security reason.
