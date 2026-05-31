#!/usr/bin/env python3
"""Regenerate the SECTIONS array in catalog.js from done/<Game>/*.webp.

Usage:
    python3 tools/gen_catalog.py

Reads the existing KEYCHAIN block from catalog.js and preserves it verbatim,
then rewrites the SECTIONS array based on what's actually on disk. Tiers are
hand-overridden for a few standout icons and otherwise auto-assigned by a
deterministic hash so they stay stable across runs.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

GAMES = [
    {
        "id": "rv",
        "title": "Rivals",
        "dir": "done/Rivals",
        "logo": "logos/rivals.webp",
        "blurb": "Real keychains from the Rivals arena. Pick your weapon (or two).",
    },
    {
        "id": "bf",
        "title": "Blox Fruits",
        "dir": "done/BloxFruits",
        "logo": "logos/bloxfruits.webp",
        "blurb": "Forty-one devil fruits. Eat them with your eyes only — they're plastic.",
    },
    {
        "id": "am",
        "title": "Adopt Me!",
        "dir": "done/Adopt Me!",
        "logo": "logos/adoptme.webp",
        "blurb": "All the pets — from common chickens to mythic dragons.",
    },
]

# Hand-curated tier overrides. (game_id, display_name) -> tier.
# Anything not listed gets a deterministic auto-tier from the hash below.
TIER_OVERRIDES = {
    # Rivals — keep the original feel
    ("rv", "War Horn"): "MYTHIC",
    ("rv", "Scythe"): "LEGENDARY",
    ("rv", "RPG"): "LEGENDARY",
    ("rv", "Flamethrower"): "LEGENDARY",
    ("rv", "Sniper"): "EPIC",
    ("rv", "Katana"): "EPIC",
    ("rv", "Assault Rifle"): "EPIC",
    ("rv", "Shorty"): "RARE",
    ("rv", "Crossbow"): "RARE",
    ("rv", "Knife"): "COMMON",
    ("rv", "Grenade"): "COMMON",
    ("rv", "Minigun"): "LEGENDARY",
    ("rv", "Chainsaw"): "EPIC",
    ("rv", "Riot Shield"): "EPIC",
    # Blox Fruits — preserve previous picks
    ("bf", "Dragon Fruit"): "MYTHIC",
    ("bf", "Dough Fruit"): "MYTHIC",
    ("bf", "Kitsune Fruit"): "MYTHIC",
    ("bf", "T-Rex Fruit"): "MYTHIC",
    ("bf", "Spirit Fruit"): "MYTHIC",
    ("bf", "Control Fruit"): "MYTHIC",
    # Adopt Me! — iconic mythics
    ("am", "Shadow Dragon"): "MYTHIC",
    ("am", "Frost Dragon"): "MYTHIC",
    ("am", "Bat Dragon"): "MYTHIC",
    ("am", "Owl"): "LEGENDARY",
    ("am", "Parrot"): "LEGENDARY",
}

TIERS = ["COMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"]


def display_name(stem: str) -> str:
    """'Animated_Frostbite_Bear_&_Cub_' -> 'Animated Frostbite Bear & Cub'."""
    s = stem.replace("_", " ").strip()
    return re.sub(r"\s+", " ", s)


def auto_tier(name: str) -> str:
    lo = name.lower()
    if any(k in lo for k in ("dragon", "phoenix", "kitsune", "t-rex")):
        return "MYTHIC"
    if any(
        k in lo
        for k in (
            "frost", "crystal", "unicorn", "demon", "ghost", "skeleton",
            "lava", "nightmare", "fairy", "robot", "shadow", "mythic",
        )
    ):
        return "LEGENDARY"
    if any(
        k in lo
        for k in (
            " cat", " dog", "puppy", "kitten", "bunny", "rabbit", "chicken",
            "hen", "duck", "frog", "fish", "cow", "pig", "horse", "bee",
            "mouse", "rat", "hamster",
        )
    ):
        return "COMMON"
    # Stable pseudo-random for the rest, weighted toward RARE/EPIC.
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    pool = ["RARE", "RARE", "RARE", "EPIC", "EPIC", "LEGENDARY"]
    return pool[h % len(pool)]


def js_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_sections() -> tuple[str, int]:
    lines: list[str] = ["export const SECTIONS = ["]
    total = 0
    for g in GAMES:
        d = os.path.join(ROOT, g["dir"])
        if not os.path.isdir(d):
            print(f"warning: {d} does not exist; skipping", file=sys.stderr)
            continue
        files = sorted(f for f in os.listdir(d) if f.endswith(".webp"))
        lines.append("  {")
        lines.append(f"    id: {js_string(g['id'])},")
        lines.append(f"    title: {js_string(g['title'])},")
        lines.append(f"    logo: {js_string(g['logo'])},")
        lines.append(f"    blurb: {js_string(g['blurb'])},")
        lines.append("    icons: [")
        for fn in files:
            stem = os.path.splitext(fn)[0]
            name = display_name(stem)
            tier = TIER_OVERRIDES.get((g["id"], name)) or auto_tier(name)
            assert tier in TIERS, f"bad tier {tier!r} for {name}"
            image = f"{g['dir']}/{fn}"
            lines.append(
                f"      {{ name: {js_string(name)}, "
                f"image: {js_string(image)}, "
                f"tier: {js_string(tier)} }},"
            )
            total += 1
        lines.append("    ],")
        lines.append("  },")
    lines.append("];")
    return "\n".join(lines), total


def main() -> None:
    catalog_path = os.path.join(ROOT, "catalog.js")
    try:
        with open(catalog_path) as f:
            existing = f.read()
    except FileNotFoundError:
        existing = ""

    keychain_match = re.search(
        r"export const KEYCHAIN\s*=\s*\{[\s\S]*?\};", existing
    )
    keychain_block = (
        keychain_match.group(0)
        if keychain_match
        else (
            'export const KEYCHAIN = {\n'
            '  name: "Custom 2-Sided Keychain",\n'
            '  price: 3,\n'
            '  paymentLink: "https://buy.stripe.com/REPLACE_ME",\n'
            "};"
        )
    )

    sections_block, total = build_sections()

    new = "\n".join([
        "// ============================================================",
        "// STAN'S LOOT DROP — catalog (auto-generated by tools/gen_catalog.py)",
        "// ============================================================",
        "// Re-run after adding/removing icons:  python3 tools/gen_catalog.py",
        "// The KEYCHAIN block above is preserved verbatim across regens, so",
        "// hand-edits to price / paymentLink survive. Tier hand-edits in the",
        "// SECTIONS array do NOT — encode those in TIER_OVERRIDES inside",
        "// tools/gen_catalog.py instead.",
        "// ============================================================",
        "",
        'export const CURRENCY = "£";',
        "",
        keychain_block,
        "",
        sections_block,
        "",
    ])

    with open(catalog_path, "w") as f:
        f.write(new)
    print(f"wrote {catalog_path} with {total} icons")


if __name__ == "__main__":
    main()
