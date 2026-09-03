#!/usr/bin/env python3
"""Fail-closed audit for the deployed static site and reviewed artwork."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from build_assets import validate_svg


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD_DIR = DOCS / "assets" / "cards"


def fail(message: str) -> None:
    raise AssertionError(message)


def extract_frozen_json(path: Path, variable: str) -> list:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"{re.escape(variable)}\s*=\s*Object\.freeze\((\[.*\])\);", text, re.DOTALL)
    if not match:
        fail(f"Could not extract {variable} from {path}")
    return json.loads(match.group(1))


def audit_cards() -> list[dict]:
    cards = extract_frozen_json(DOCS / "cards.js", "window.SEEK_A_CARD_CARDS")
    if len(cards) < 250:
        fail(f"Expected at least 250 reviewed cards; found {len(cards)}")

    required_keys = {"id", "label", "category", "difficulty", "image", "artwork"}
    ids = set()
    images = set()
    for card in cards:
        if set(card) != required_keys:
            fail(f"Unexpected card fields: {card}")
        if not re.fullmatch(r"[a-z0-9-]+", card["id"]):
            fail(f"Unsafe card id: {card['id']}")
        if card["id"] in ids:
            fail(f"Duplicate card id: {card['id']}")
        ids.add(card["id"])
        if not re.fullmatch(r"assets/cards/[A-F0-9-]+\.svg", card["image"]):
            fail(f"Unsafe card path: {card['image']}")
        images.add(card["image"])
        if card["difficulty"] not in {"easy", "tricky"}:
            fail(f"Unexpected difficulty: {card['difficulty']}")

    disk_images = {str(path.relative_to(DOCS)) for path in CARD_DIR.glob("*.svg")}
    if images != disk_images:
        fail(f"Card/disk image mismatch: missing={images - disk_images}, extra={disk_images - images}")
    return cards


def audit_hashes(cards: list[dict]) -> None:
    recorded = json.loads((ROOT / "ASSET_HASHES.json").read_text(encoding="utf-8"))
    expected_paths = {f"docs/{card['image']}" for card in cards}
    if set(recorded) != expected_paths:
        fail("ASSET_HASHES.json does not exactly match the card allowlist")
    for relative, expected_hash in recorded.items():
        path = ROOT / relative
        data = path.read_bytes()
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            fail(f"Hash mismatch: {relative}")
        validate_svg(data.decode("utf-8"), path.stem)


def audit_runtime(cards: list[dict]) -> None:
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    required_csp = [
        "default-src 'none'", "script-src 'self'", "style-src 'self'",
        "img-src 'self'", "connect-src 'none'", "object-src 'none'",
        "base-uri 'none'", "form-action 'none'"
    ]
    for directive in required_csp:
        if directive not in index:
            fail(f"Missing CSP directive: {directive}")

    app = (DOCS / "app.js").read_text(encoding="utf-8")
    forbidden_code = ["innerHTML", "outerHTML", "insertAdjacentHTML", "eval(", "new Function", "XMLHttpRequest", "WebSocket", "EventSource"]
    for token in forbidden_code:
        if token in app:
            fail(f"Forbidden runtime code: {token}")

    for path in DOCS.iterdir():
        if path.is_file() and path.suffix in {".html", ".css", ".js", ".webmanifest"}:
            text = path.read_text(encoding="utf-8")
            if re.search(r"https?://", text, re.IGNORECASE):
                fail(f"External runtime URL in {path.name}")

    safe_assets = extract_frozen_json(DOCS / "asset-list.js", "self.SEEK_A_CARD_SAFE_ASSETS")
    asset_list_text = (DOCS / "asset-list.js").read_text(encoding="utf-8")
    if not re.search(r'self\.SEEK_A_CARD_CACHE_NAME = "seek-a-card-[a-f0-9]{12}";', asset_list_text):
        fail("Missing content-derived service-worker cache revision")
    expected = {
        "./", "./index.html", "./styles.css", "./cards.js", "./app.js",
        "./service-worker.js", "./asset-list.js", "./manifest.webmanifest",
        "./icon.svg", "./maskable-icon.svg",
        *{f"./{card['image']}" for card in cards},
    }
    if set(safe_assets) != expected or len(safe_assets) != len(expected):
        fail("Service-worker asset allowlist is incomplete or contains extras")


def check_javascript() -> None:
    for filename in ["app.js", "cards.js", "asset-list.js", "service-worker.js"]:
        result = subprocess.run(
            ["node", "--check", str(DOCS / filename)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            fail(f"JavaScript syntax error in {filename}: {result.stderr}")


def make_contact_sheet(cards: list[dict]) -> None:
    inkscape = shutil.which("inkscape")
    if not inkscape:
        print("Contact sheet skipped: Inkscape is unavailable")
        return
    columns = 12
    cell_width = 130
    cell_height = 130
    rows = (len(cards) + columns - 1) // columns
    sheet_svg = ROOT / "audit-contact-sheet.svg"
    output = ROOT / "audit-contact-sheet.png"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{columns * cell_width}" height="{rows * cell_height}" viewBox="0 0 {columns * cell_width} {rows * cell_height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    for index, card in enumerate(cards):
        column = index % columns
        row = index // columns
        x = column * cell_width
        y = row * cell_height
        image_uri = (DOCS / card["image"]).resolve().as_uri()
        label = html.escape(card["label"])
        parts.append(f'<image href="{image_uri}" xlink:href="{image_uri}" x="{x + 20}" y="{y + 5}" width="90" height="90"/>')
        parts.append(f'<text x="{x + 65}" y="{y + 112}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#17324d">{label}</text>')
    parts.append("</svg>")
    sheet_svg.write_text("\n".join(parts), encoding="utf-8")
    subprocess.run(
        [inkscape, str(sheet_svg), "--export-type=png", f"--export-filename={output}"],
        check=True,
        capture_output=True,
    )
    sheet_svg.unlink()
    print(f"Contact sheet: {output}")


def main() -> None:
    cards = audit_cards()
    audit_hashes(cards)
    audit_runtime(cards)
    check_javascript()
    make_contact_sheet(cards)
    print(f"Audit passed: {len(cards)} cards, exact local allowlist, valid hashes and scripts")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, subprocess.CalledProcessError) as error:
        print(f"AUDIT FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
