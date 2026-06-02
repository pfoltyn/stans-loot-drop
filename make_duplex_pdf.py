#!/usr/bin/env python3
"""Generate a 2-page PDF with one icon on the front + one on the back, perfectly
centred so they align when printed double-sided on a home printer.

Why centred + same size = always-aligned: any duplex flip (long-edge or
short-edge) preserves the centre of the page; identical bounding boxes around
the page centre will land on top of each other from the laminator's POV.

Usage:
    python3 make_duplex_pdf.py <front_icon> <back_icon> [-o out.pdf]
                               [--size-mm 32] [--no-cut-marks]

Icon names accepted:
    - Full path:                  done/Rivals/Knife.png
    - Just stem (any game):       Knife          (searches done/<Game>/Knife.png)
    - "Game/Name":                Rivals/Knife
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw

# A4 in mm.
PAGE_MM = (210, 297)
DPI = 300
DONE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "done")


def mm_to_px(mm, dpi=DPI):
    return int(round(mm * dpi / 25.4))


def find_icon(name):
    """Resolve an icon name into a file path under done/."""
    if os.path.isabs(name) and os.path.exists(name):
        return name
    if os.path.exists(name):
        return os.path.abspath(name)

    # "Game/Name" form.
    if "/" in name:
        candidate = os.path.join(DONE_DIR, name)
        for ext in (".png", ".webp", ".jpg", ".jpeg"):
            if os.path.exists(candidate + ext):
                return candidate + ext
            if name.lower().endswith(ext) and os.path.exists(candidate):
                return candidate

    # Bare name — search every game folder.
    stem_lower = os.path.splitext(name)[0].lower()
    matches = []
    for game in sorted(os.listdir(DONE_DIR)):
        game_dir = os.path.join(DONE_DIR, game)
        if not os.path.isdir(game_dir):
            continue
        for f in os.listdir(game_dir):
            f_stem, ext = os.path.splitext(f)
            if ext.lower() not in (".png", ".webp", ".jpg", ".jpeg"):
                continue
            if f_stem.lower() == stem_lower:
                matches.append(os.path.join(game_dir, f))

    if not matches:
        raise FileNotFoundError(
            f"No icon found matching {name!r}. Try a full path like "
            f"'done/Rivals/Knife.png' or 'Rivals/Knife'."
        )
    if len(matches) > 1:
        # Prefer .png (the print-ready master) over .webp.
        png = [m for m in matches if m.endswith(".png")]
        if len(png) == 1:
            return png[0]
        raise ValueError(
            f"Multiple icons match {name!r}: " + ", ".join(matches) +
            ". Disambiguate with 'Game/Name'."
        )
    return matches[0]


def build_page(icon_path, size_px, cut_marks=True):
    """Render one A4 page (white) with the icon centred at the given size."""
    page_w = mm_to_px(PAGE_MM[0])
    page_h = mm_to_px(PAGE_MM[1])
    page = Image.new("RGB", (page_w, page_h), "white")

    icon = Image.open(icon_path).convert("RGBA")
    # Scale icon to a fixed *bounding box* so front and back align perfectly.
    icon = icon.resize((size_px, size_px), Image.LANCZOS)

    x0 = (page_w - size_px) // 2
    y0 = (page_h - size_px) // 2
    page.paste(icon, (x0, y0), icon)

    if cut_marks:
        d = ImageDraw.Draw(page)
        tick = mm_to_px(4)
        gap = mm_to_px(2)
        ink = (140, 140, 140)
        thick = max(1, mm_to_px(0.15))
        # Four corners — short L-shaped ticks offset outside the icon.
        for cx, cy, dx, dy in [
            (x0, y0, -1, -1),
            (x0 + size_px, y0,  1, -1),
            (x0, y0 + size_px, -1,  1),
            (x0 + size_px, y0 + size_px,  1,  1),
        ]:
            # Horizontal tick
            d.line(
                [(cx + dx * gap, cy), (cx + dx * (gap + tick), cy)],
                fill=ink, width=thick,
            )
            # Vertical tick
            d.line(
                [(cx, cy + dy * gap), (cx, cy + dy * (gap + tick))],
                fill=ink, width=thick,
            )

    return page


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("front", help="Front icon (name, Game/Name, or path)")
    p.add_argument("back",  help="Back icon (name, Game/Name, or path)")
    p.add_argument("-o", "--output", default="duplex_keychain.pdf",
                   help="Output PDF path (default: duplex_keychain.pdf)")
    p.add_argument("--size-mm", type=float, default=32.0,
                   help="Icon side length in mm (default 32 — matches Stan's 3.2cm cards)")
    p.add_argument("--no-cut-marks", action="store_true",
                   help="Don't draw cut marks around the icon")
    args = p.parse_args()

    try:
        front_path = find_icon(args.front)
        back_path = find_icon(args.back)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"front: {front_path}")
    print(f"back:  {back_path}")

    size_px = mm_to_px(args.size_mm)
    cut_marks = not args.no_cut_marks
    page_front = build_page(front_path, size_px, cut_marks=cut_marks)
    page_back = build_page(back_path, size_px, cut_marks=cut_marks)

    # Multi-page PDF: save the first page, then append the second.
    page_front.save(
        args.output,
        format="PDF",
        resolution=DPI,
        save_all=True,
        append_images=[page_back],
    )
    print(f"wrote {args.output}  (A4, {args.size_mm:g} mm icon, duplex-ready)")
    print("print with: long-edge flip duplex (default on most printers)")


if __name__ == "__main__":
    main()
