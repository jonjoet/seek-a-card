#!/usr/bin/env python3
"""Build the reviewed, local-only card deck from a pinned OpenMoji revision."""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets" / "cards"
OPENMOJI_COMMIT = "aeb8bb3a59e2de39c754ac79180c8131c906acea"
OPENMOJI_BASE = (
    "https://raw.githubusercontent.com/hfg-gmuend/openmoji/"
    f"{OPENMOJI_COMMIT}/color/svg"
)
OPENMOJI_DATA = (
    "https://raw.githubusercontent.com/hfg-gmuend/openmoji/"
    f"{OPENMOJI_COMMIT}/data/openmoji.json"
)

# This is the complete content allowlist. Nothing discovered from the network is
# added automatically. Each tuple is (label, OpenMoji hexcode, difficulty).
CARD_GROUPS = {
    "Animals": [
        ("Dog", "1F436", "easy"), ("Cat", "1F431", "easy"),
        ("Mouse", "1F42D", "easy"), ("Hamster", "1F439", "easy"),
        ("Rabbit", "1F430", "easy"), ("Fox", "1F98A", "easy"),
        ("Bear", "1F43B", "easy"), ("Panda", "1F43C", "easy"),
        ("Koala", "1F428", "easy"), ("Tiger", "1F42F", "easy"),
        ("Lion", "1F981", "easy"), ("Cow", "1F42E", "easy"),
        ("Pig", "1F437", "easy"), ("Frog", "1F438", "easy"),
        ("Monkey", "1F435", "easy"), ("Chicken", "1F414", "easy"),
        ("Penguin", "1F427", "easy"), ("Bird", "1F426", "easy"),
        ("Duck", "1F986", "easy"), ("Owl", "1F989", "easy"),
        ("Horse", "1F434", "easy"), ("Sheep", "1F411", "easy"),
        ("Goat", "1F410", "easy"), ("Elephant", "1F418", "easy"),
        ("Giraffe", "1F992", "easy"), ("Zebra", "1F993", "easy"),
        ("Turtle", "1F422", "easy"), ("Snake", "1F40D", "easy"),
        ("Fish", "1F41F", "easy"), ("Whale", "1F40B", "easy"),
        ("Dolphin", "1F42C", "easy"), ("Shark", "1F988", "easy"),
        ("Octopus", "1F419", "easy"), ("Crab", "1F980", "easy"),
        ("Snail", "1F40C", "easy"), ("Butterfly", "1F98B", "easy"),
        ("Ant", "1F41C", "easy"), ("Bee", "1F41D", "easy"),
        ("Ladybug", "1F41E", "easy"), ("Spider", "1F577", "easy"),
        ("Wolf", "1F43A", "tricky"), ("Raccoon", "1F99D", "tricky"),
        ("Leopard", "1F406", "tricky"), ("Moose", "1FACE", "tricky"),
        ("Deer", "1F98C", "tricky"), ("Bison", "1F9AC", "tricky"),
        ("Llama", "1F999", "tricky"), ("Rhinoceros", "1F98F", "tricky"),
        ("Hippopotamus", "1F99B", "tricky"), ("Kangaroo", "1F998", "tricky"),
        ("Sloth", "1F9A5", "tricky"), ("Otter", "1F9A6", "tricky"),
        ("Skunk", "1F9A8", "tricky"), ("Hedgehog", "1F994", "tricky"),
        ("Bat", "1F987", "tricky"), ("Eagle", "1F985", "tricky"),
        ("Turkey", "1F983", "tricky"), ("Rooster", "1F413", "tricky"),
        ("Flamingo", "1F9A9", "tricky"), ("Peacock", "1F99A", "tricky"),
        ("Parrot", "1F99C", "tricky"), ("Crocodile", "1F40A", "tricky"),
        ("Lizard", "1F98E", "tricky"), ("Dinosaur", "1F995", "tricky"),
        ("T-Rex", "1F996", "tricky"), ("Seal", "1F9AD", "tricky"),
        ("Lobster", "1F99E", "tricky"), ("Worm", "1FAB1", "tricky"),
    ],
    "Food": [
        ("Apple", "1F34E", "easy"), ("Pear", "1F350", "easy"),
        ("Orange", "1F34A", "easy"), ("Lemon", "1F34B", "easy"),
        ("Banana", "1F34C", "easy"), ("Watermelon", "1F349", "easy"),
        ("Grapes", "1F347", "easy"), ("Strawberry", "1F353", "easy"),
        ("Blueberries", "1FAD0", "easy"), ("Cherries", "1F352", "easy"),
        ("Peach", "1F351", "easy"), ("Mango", "1F96D", "easy"),
        ("Pineapple", "1F34D", "easy"), ("Coconut", "1F965", "easy"),
        ("Kiwi", "1F95D", "easy"), ("Tomato", "1F345", "easy"),
        ("Avocado", "1F951", "easy"), ("Potato", "1F954", "easy"),
        ("Carrot", "1F955", "easy"), ("Corn", "1F33D", "easy"),
        ("Cucumber", "1F952", "easy"), ("Broccoli", "1F966", "easy"),
        ("Mushroom", "1F344", "easy"), ("Bread", "1F35E", "easy"),
        ("Cheese", "1F9C0", "easy"), ("Egg", "1F95A", "easy"),
        ("Pancakes", "1F95E", "easy"), ("Waffle", "1F9C7", "easy"),
        ("Hamburger", "1F354", "easy"), ("French fries", "1F35F", "easy"),
        ("Pizza", "1F355", "easy"), ("Hot dog", "1F32D", "easy"),
        ("Taco", "1F32E", "easy"), ("Popcorn", "1F37F", "easy"),
        ("Ice cream", "1F368", "easy"), ("Donut", "1F369", "easy"),
        ("Cookie", "1F36A", "easy"), ("Cupcake", "1F9C1", "easy"),
        ("Birthday cake", "1F382", "easy"), ("Lollipop", "1F36D", "easy"),
        ("Baby bottle", "1F37C", "easy"), ("Bell pepper", "1FAD1", "tricky"),
        ("Eggplant", "1F346", "tricky"), ("Peanuts", "1F95C", "tricky"),
        ("Pretzel", "1F968", "tricky"), ("Croissant", "1F950", "tricky"),
        ("Bagel", "1F96F", "tricky"), ("Sandwich", "1F96A", "tricky"),
        ("Rice", "1F35A", "tricky"), ("Spaghetti", "1F35D", "tricky"),
        ("Soup", "1F372", "tricky"), ("Juice box", "1F9C3", "tricky"),
    ],
    "Things": [
        ("Balloon", "1F388", "easy"), ("Gift", "1F381", "easy"),
        ("Soccer ball", "26BD", "easy"), ("Basketball", "1F3C0", "easy"),
        ("Baseball", "26BE", "easy"), ("Football", "1F3C8", "easy"),
        ("Tennis ball", "1F3BE", "easy"), ("Volleyball", "1F3D0", "easy"),
        ("Frisbee", "1F94F", "easy"), ("Kite", "1FA81", "easy"),
        ("Yo-yo", "1FA80", "easy"), ("Puzzle piece", "1F9E9", "easy"),
        ("Teddy bear", "1F9F8", "easy"), ("Video game", "1F3AE", "easy"),
        ("Book", "1F4D6", "easy"), ("Pencil", "270F", "easy"),
        ("Crayon", "1F58D", "easy"), ("Paintbrush", "1F58C", "easy"),
        ("Scissors", "2702", "easy"), ("Ruler", "1F4CF", "easy"),
        ("Backpack", "1F392", "easy"), ("Glasses", "1F453", "easy"),
        ("Sunglasses", "1F576", "easy"), ("Hat", "1F9E2", "easy"),
        ("Crown", "1F451", "easy"), ("Shirt", "1F455", "easy"),
        ("Jeans", "1F456", "easy"), ("Dress", "1F457", "easy"),
        ("Sock", "1F9E6", "easy"), ("Shoe", "1F45F", "easy"),
        ("Boot", "1F97E", "easy"), ("Glove", "1F9E4", "easy"),
        ("Scarf", "1F9E3", "easy"), ("Umbrella", "2614", "easy"),
        ("Watch", "231A", "easy"), ("Phone", "1F4F1", "easy"),
        ("Computer", "1F4BB", "easy"), ("Keyboard", "2328", "easy"),
        ("Camera", "1F4F7", "easy"), ("Television", "1F4FA", "easy"),
        ("Light bulb", "1F4A1", "easy"), ("Flashlight", "1F526", "easy"),
        ("Bell", "1F514", "easy"), ("Key", "1F511", "easy"),
        ("Lock", "1F512", "easy"), ("Magnet", "1F9F2", "easy"),
        ("Hammer", "1F528", "easy"), ("Wrench", "1F527", "easy"),
        ("Broom", "1F9F9", "easy"), ("Basket", "1F9FA", "easy"),
        ("Soap", "1F9FC", "easy"), ("Sponge", "1F9FD", "easy"),
        ("Toothbrush", "1FAA5", "easy"), ("Bathtub", "1F6C1", "easy"),
        ("Toilet", "1F6BD", "easy"), ("Bed", "1F6CF", "easy"),
        ("Chair", "1FA91", "easy"), ("Door", "1F6AA", "easy"),
        ("Window", "1FA9F", "easy"), ("Bowling ball", "1F3B3", "tricky"),
        ("Nesting dolls", "1FA86", "tricky"), ("Abacus", "1F9EE", "tricky"),
        ("Toolbox", "1F9F0", "tricky"), ("Toilet paper", "1F9FB", "tricky"),
    ],
    "On the go": [
        ("Car", "1F697", "easy"), ("Taxi", "1F695", "easy"),
        ("Bus", "1F68C", "easy"), ("Race car", "1F3CE", "easy"),
        ("Police car", "1F693", "easy"), ("Ambulance", "1F691", "easy"),
        ("Fire truck", "1F692", "easy"), ("Truck", "1F69A", "easy"),
        ("Tractor", "1F69C", "easy"), ("Scooter", "1F6F4", "easy"),
        ("Bicycle", "1F6B2", "easy"), ("Motorcycle", "1F3CD", "easy"),
        ("Train", "1F686", "easy"), ("Airplane", "2708", "easy"),
        ("Helicopter", "1F681", "easy"), ("Rocket", "1F680", "easy"),
        ("Sailboat", "26F5", "easy"), ("Speedboat", "1F6A4", "easy"),
        ("Canoe", "1F6F6", "easy"), ("House", "1F3E0", "easy"),
        ("School", "1F3EB", "easy"), ("Hospital", "1F3E5", "easy"),
        ("Castle", "1F3F0", "easy"), ("Tent", "26FA", "easy"),
        ("Subway", "1F687", "tricky"), ("Stadium", "1F3DF", "tricky"),
        ("Circus tent", "1F3AA", "tricky"), ("Fountain", "26F2", "tricky"),
        ("Bridge", "1F309", "tricky"),
    ],
    "Nature": [
        ("Sun", "2600", "easy"), ("Moon", "1F319", "easy"),
        ("Star", "2B50", "easy"), ("Cloud", "2601", "easy"),
        ("Rain cloud", "1F327", "easy"), ("Snowman", "2603", "easy"),
        ("Snowflake", "2744", "easy"), ("Lightning", "1F329", "easy"),
        ("Rainbow", "1F308", "easy"), ("Fire", "1F525", "easy"),
        ("Water drop", "1F4A7", "easy"), ("Ocean wave", "1F30A", "easy"),
        ("Tree", "1F333", "easy"), ("Palm tree", "1F334", "easy"),
        ("Cactus", "1F335", "easy"), ("Seedling", "1F331", "easy"),
        ("Flower", "1F33C", "easy"), ("Sunflower", "1F33B", "easy"),
        ("Rose", "1F339", "easy"), ("Tulip", "1F337", "easy"),
        ("Leaf", "1F343", "easy"), ("Maple leaf", "1F341", "easy"),
        ("Four-leaf clover", "1F340", "tricky"), ("Nest with eggs", "1FABA", "tricky"),
        ("Rock", "1FAA8", "tricky"), ("Mountain", "26F0", "tricky"),
        ("Volcano", "1F30B", "tricky"), ("Desert island", "1F3DD", "tricky"),
        ("Globe", "1F30E", "tricky"), ("Comet", "2604", "tricky"),
        ("Tornado", "1F32A", "tricky"),
    ],
    "Shapes & colors": [
        ("Red circle", "1F534", "easy"), ("Orange circle", "1F7E0", "easy"),
        ("Yellow circle", "1F7E1", "easy"), ("Green circle", "1F7E2", "easy"),
        ("Blue circle", "1F535", "easy"), ("Purple circle", "1F7E3", "easy"),
        ("Brown circle", "1F7E4", "easy"), ("Black circle", "26AB", "easy"),
        ("White circle", "26AA", "easy"), ("Red square", "1F7E5", "easy"),
        ("Orange square", "1F7E7", "easy"), ("Yellow square", "1F7E8", "easy"),
        ("Green square", "1F7E9", "easy"), ("Blue square", "1F7E6", "easy"),
        ("Purple square", "1F7EA", "easy"), ("Brown square", "1F7EB", "easy"),
        ("Black square", "2B1B", "easy"), ("White square", "2B1C", "easy"),
        ("Red heart", "2764", "easy"), ("Orange heart", "1F9E1", "easy"),
        ("Yellow heart", "1F49B", "easy"), ("Green heart", "1F49A", "easy"),
        ("Blue heart", "1F499", "easy"), ("Purple heart", "1F49C", "easy"),
        ("Brown heart", "1F90E", "easy"), ("Black heart", "1F5A4", "easy"),
        ("White heart", "1F90D", "easy"), ("Blue diamond", "1F537", "tricky"),
        ("Up triangle", "1F53A", "tricky"), ("Down triangle", "1F53B", "tricky"),
    ],
}

ALLOWED_TAGS = {
    "svg", "g", "path", "circle", "ellipse", "line", "polyline", "polygon", "rect"
}
FORBIDDEN_TEXT = re.compile(
    r"<\s*(script|foreignObject|iframe|image|use|style)\b|\bon[a-z]+\s*=|"
    r"\b(?:href|src)\s*=|url\s*\(",
    re.IGNORECASE,
)


def slugify(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def validate_svg(text: str, expected_hex: str) -> None:
    if FORBIDDEN_TEXT.search(text):
        raise ValueError(f"Forbidden SVG content in {expected_hex}")
    root = ET.fromstring(text)
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in ALLOWED_TAGS:
            raise ValueError(f"Unexpected <{tag}> in {expected_hex}")
        for name, value in element.attrib.items():
            local_name = name.rsplit("}", 1)[-1].lower()
            if local_name.startswith("on") or local_name in {"href", "src"}:
                raise ValueError(f"Unsafe attribute {name} in {expected_hex}")
            if "url(" in value.lower() or "http:" in value.lower() or "https:" in value.lower():
                raise ValueError(f"External reference in {expected_hex}")


def download_svg(hexcode: str) -> bytes:
    destination = ASSETS / f"{hexcode}.svg"
    if destination.exists():
        data = destination.read_bytes()
        validate_svg(data.decode("utf-8"), hexcode)
        return data
    request = urllib.request.Request(
        f"{OPENMOJI_BASE}/{hexcode}.svg",
        headers={"User-Agent": "seek-a-card-build/1.0"},
    )
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read()
            break
        except Exception as error:
            last_error = error
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    if last_error is not None and "data" not in locals():
        raise last_error
    text = data.decode("utf-8")
    validate_svg(text, hexcode)
    destination.write_bytes(data)
    return data


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    cards = []
    hashes = {}
    seen_ids = set()
    seen_hex = set()

    metadata_request = urllib.request.Request(
        OPENMOJI_DATA,
        headers={"User-Agent": "seek-a-card-build/1.0"},
    )
    with urllib.request.urlopen(metadata_request, timeout=60) as response:
        metadata = json.loads(response.read().decode("utf-8"))
    metadata_by_hex = {item["hexcode"]: item for item in metadata}

    all_hex = [hexcode for specs in CARD_GROUPS.values() for _, hexcode, _ in specs]
    allowed_hex = set(all_hex)
    for stale_asset in ASSETS.glob("*.svg"):
        if stale_asset.stem not in allowed_hex:
            stale_asset.unlink()
    downloaded = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(download_svg, hexcode): hexcode for hexcode in all_hex}
        for future in as_completed(futures):
            hexcode = futures[future]
            downloaded[hexcode] = future.result()

    for category, specs in CARD_GROUPS.items():
        for label, hexcode, difficulty in specs:
            card_id = slugify(label)
            if card_id in seen_ids:
                raise ValueError(f"Duplicate card id: {card_id}")
            if hexcode in seen_hex:
                raise ValueError(f"Duplicate artwork: {hexcode}")
            seen_ids.add(card_id)
            seen_hex.add(hexcode)

            data = downloaded[hexcode]
            destination = ASSETS / f"{hexcode}.svg"
            destination.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            hashes[f"docs/assets/cards/{hexcode}.svg"] = digest
            cards.append({
                "id": card_id,
                "label": label,
                "category": category,
                "difficulty": difficulty,
                "image": f"assets/cards/{hexcode}.svg",
                "artwork": hexcode,
            })

    cards_js = "/* Generated by tools/build_assets.py. */\nwindow.SEEK_A_CARD_CARDS = Object.freeze(" + json.dumps(cards, indent=2) + ");\n"
    (DOCS / "cards.js").write_text(cards_js, encoding="utf-8")

    safe_assets = [
        "./", "./index.html", "./styles.css", "./cards.js", "./app.js",
        "./service-worker.js", "./asset-list.js",
        "./manifest.webmanifest", "./icon.svg", "./maskable-icon.svg",
        *[f"./assets/cards/{card['artwork']}.svg" for card in cards],
    ]
    revision_material = cards_js + "".join(f"{path}:{digest}\n" for path, digest in sorted(hashes.items()))
    cache_revision = hashlib.sha256(revision_material.encode("utf-8")).hexdigest()[:12]
    asset_list_js = (
        "/* Generated by tools/build_assets.py. */\n"
        f'self.SEEK_A_CARD_CACHE_NAME = "seek-a-card-{cache_revision}";\n'
        "self.SEEK_A_CARD_SAFE_ASSETS = Object.freeze(" + json.dumps(safe_assets, indent=2) + ");\n"
    )
    (DOCS / "asset-list.js").write_text(asset_list_js, encoding="utf-8")

    hash_path = ROOT / "ASSET_HASHES.json"
    hash_path.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    notice = [
        "# Third-party artwork notices",
        "",
        "The application code is licensed under the repository's MIT License. The",
        "bundled card artwork is **not** covered by that license.",
        "",
        "All card illustrations are from [OpenMoji](https://openmoji.org/), used under",
        "the [Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/).",
        "The files are unmodified copies from pinned OpenMoji commit",
        f"[`{OPENMOJI_COMMIT}`](https://github.com/hfg-gmuend/openmoji/tree/{OPENMOJI_COMMIT}).",
        "OpenMoji is the open-source emoji and icon project of HfG Schwäbisch Gmünd.",
        "",
        "## Included illustrations",
        "",
        "| Card | OpenMoji file | OpenMoji author |",
        "|---|---|---|",
    ]
    for card in cards:
        item = metadata_by_hex.get(card["artwork"])
        if not item or not item.get("openmoji_author"):
            raise ValueError(f"Missing attribution metadata for {card['artwork']}")
        author = item["openmoji_author"].replace("|", "\\|")
        notice.append(f"| {card['label']} | `{card['artwork']}.svg` | {author} |")
    notice.append("")
    (ROOT / "THIRD_PARTY_NOTICES.md").write_text("\n".join(notice), encoding="utf-8")

    print(f"Built {len(cards)} reviewed cards across {len(CARD_GROUPS)} categories")


if __name__ == "__main__":
    main()
