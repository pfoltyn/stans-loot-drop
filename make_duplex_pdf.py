#!/usr/bin/env python3
"""Generate a print-ready PDF that aligns icons on the front + back of each
sheet when printed double-sided.

Each page places one icon at the centre of an A4 sheet at a fixed bounding box.
Centring + identical box = the back lands on top of the front under any duplex
flip — IN THEORY. In practice your printer's duplex unit may have a small
horizontal/vertical registration offset (a hardware quirk, common). To
compensate, use --back-offset-x / --back-offset-y to nudge the *back-page* icon
in millimetres. Dial it in once for your printer; the same value will work
forever.

Usage (single pair):
    python3 make_duplex_pdf.py <front_icon> <back_icon> [-o out.pdf]
                               [--size-mm 32] [--no-cut-marks]
                               [--back-offset-x -2] [--back-offset-y 0]

Usage (batch — many keychains tiled per sheet):
    python3 make_duplex_pdf.py --batch pairs.txt [-o out.pdf] ...

    pairs.txt: one keychain per line, two whitespace-separated icon names.
    Blank lines and lines starting with `#` are ignored.

        # frontside           backside
        Knife                 Dragon_Fruit
        Phoenix_              Adopt Me!/Bee_

    Batch mode tiles all pairs onto a grid: page 1 holds every front, page 2
    holds every back (mirrored horizontally so a long-edge duplex flip aligns
    each back over its front). When more pairs are supplied than fit on one
    sheet, output paginates as front, back, front, back, ...

    Use --flip short-edge if your printer flips around the horizontal edge
    instead. Use --margin-mm / --grid-gap-mm to control sheet padding and the
    space between adjacent cells.

Icon names accepted:
    - Full path:                  done/Rivals/Knife.png
    - Just stem (any game):       Knife          (searches done/<Game>/Knife.png)
    - "Game/Name":                Rivals/Knife
"""

import argparse
import math
import os
import shlex
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


def build_page(icon_path, size_px, cut_marks=True, offset_px=(0, 0)):
    """Render one A4 page (white) with the icon centred at the given size,
    optionally shifted by ``offset_px`` (px, +x = right, +y = down).
    """
    page_w = mm_to_px(PAGE_MM[0])
    page_h = mm_to_px(PAGE_MM[1])
    page = Image.new("RGB", (page_w, page_h), "white")

    icon = Image.open(icon_path).convert("RGBA")
    icon = icon.resize((size_px, size_px), Image.LANCZOS)

    ox, oy = offset_px
    x0 = (page_w - size_px) // 2 + ox
    y0 = (page_h - size_px) // 2 + oy
    page.paste(icon, (x0, y0), icon)

    if cut_marks:
        d = ImageDraw.Draw(page)
        tick = mm_to_px(4)
        gap = mm_to_px(2)
        ink = (140, 140, 140)
        thick = max(1, mm_to_px(0.15))
        # Cut marks always trace the icon's *true centred* position so cutting
        # is consistent across the stack — the offset is for printer
        # registration, not for where you actually want the icon to land.
        cut_x0 = (page_w - size_px) // 2
        cut_y0 = (page_h - size_px) // 2
        for cx, cy, dx, dy in [
            (cut_x0, cut_y0, -1, -1),
            (cut_x0 + size_px, cut_y0,  1, -1),
            (cut_x0, cut_y0 + size_px, -1,  1),
            (cut_x0 + size_px, cut_y0 + size_px,  1,  1),
        ]:
            d.line(
                [(cx + dx * gap, cy), (cx + dx * (gap + tick), cy)],
                fill=ink, width=thick,
            )
            d.line(
                [(cx, cy + dy * gap), (cx, cy + dy * (gap + tick))],
                fill=ink, width=thick,
            )

    return page


def _draw_cut_marks(draw, cell_x0, cell_y0, cell_x1, cell_y1):
    tick = mm_to_px(4)
    gap = mm_to_px(2)
    ink = (140, 140, 140)
    thick = max(1, mm_to_px(0.15))
    for cx, cy, dx, dy in [
        (cell_x0, cell_y0, -1, -1),
        (cell_x1, cell_y0,  1, -1),
        (cell_x0, cell_y1, -1,  1),
        (cell_x1, cell_y1,  1,  1),
    ]:
        draw.line([(cx + dx * gap, cy), (cx + dx * (gap + tick), cy)],
                  fill=ink, width=thick)
        draw.line([(cx, cy + dy * gap), (cx, cy + dy * (gap + tick))],
                  fill=ink, width=thick)


def build_grid_page(cells, cols, rows, cell_px, gap_px, cut_marks=True, offset_px=(0, 0)):
    """Render an A4 page with a cols x rows grid of icons centred on the sheet.

    ``cells`` is an iterable of (row, col, icon_path); missing cells stay blank.
    ``offset_px`` shifts every icon by the same amount (printer-registration
    compensation); cut marks always trace the unshifted cell so the cutting
    grid stays consistent.
    """
    page_w = mm_to_px(PAGE_MM[0])
    page_h = mm_to_px(PAGE_MM[1])
    page = Image.new("RGB", (page_w, page_h), "white")

    grid_w = cols * cell_px + (cols - 1) * gap_px
    grid_h = rows * cell_px + (rows - 1) * gap_px
    grid_x0 = (page_w - grid_w) // 2
    grid_y0 = (page_h - grid_h) // 2

    ox, oy = offset_px

    for row, col, icon_path in cells:
        cell_x0 = grid_x0 + col * (cell_px + gap_px)
        cell_y0 = grid_y0 + row * (cell_px + gap_px)
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize((cell_px, cell_px), Image.LANCZOS)
        page.paste(icon, (cell_x0 + ox, cell_y0 + oy), icon)

    if cut_marks:
        d = ImageDraw.Draw(page)
        for row in range(rows):
            for col in range(cols):
                cell_x0 = grid_x0 + col * (cell_px + gap_px)
                cell_y0 = grid_y0 + row * (cell_px + gap_px)
                _draw_cut_marks(d, cell_x0, cell_y0,
                                cell_x0 + cell_px, cell_y0 + cell_px)

    return page


def pick_grid(n_pairs, cell_px, gap_px, margin_px):
    """Choose a (cols, rows, per_sheet) grid that fits within the A4 margins.

    If everything fits on one sheet, prefer a near-square grid so the layout
    isn't lopsided. Otherwise use the maximum grid that fits per sheet and
    paginate the input across multiple sheets.
    """
    page_w = mm_to_px(PAGE_MM[0])
    page_h = mm_to_px(PAGE_MM[1])
    avail_w = page_w - 2 * margin_px
    avail_h = page_h - 2 * margin_px
    pitch = cell_px + gap_px
    # +gap_px because the last cell doesn't need a trailing gap.
    max_cols = max(1, (avail_w + gap_px) // pitch)
    max_rows = max(1, (avail_h + gap_px) // pitch)
    per_max = max_cols * max_rows

    if n_pairs <= per_max:
        cols = min(max_cols, max(1, math.ceil(math.sqrt(n_pairs))))
        rows = min(max_rows, max(1, math.ceil(n_pairs / cols)))
        return cols, rows, cols * rows

    return max_cols, max_rows, per_max


def parse_batch_file(path):
    """Yield (front_token, back_token) for each non-blank line."""
    with open(path) as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = shlex.split(line)
            if len(parts) != 2:
                raise ValueError(
                    f"{path}:{lineno}: expected exactly two icon names per line, got {len(parts)}: {line!r}"
                )
            yield parts[0], parts[1]


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("front", nargs="?", help="Front icon (single-pair mode)")
    p.add_argument("back",  nargs="?", help="Back icon (single-pair mode)")
    p.add_argument("--batch", help="Read pairs from a file (one per line)")
    p.add_argument("-o", "--output", default="duplex_keychain.pdf",
                   help="Output PDF path (default: duplex_keychain.pdf)")
    p.add_argument("--size-mm", type=float, default=32.0,
                   help="Icon side length in mm (default 32 — matches Stan's 3.2cm cards)")
    p.add_argument("--no-cut-marks", action="store_true",
                   help="Don't draw cut marks around each icon")
    p.add_argument("--back-offset-x", type=float, default=0.0,
                   help="Shift the BACK icon horizontally in mm (negative = left). "
                        "Use this to compensate for your printer's duplex registration offset.")
    p.add_argument("--back-offset-y", type=float, default=0.0,
                   help="Shift the BACK icon vertically in mm (negative = up).")
    p.add_argument("--front-offset-x", type=float, default=0.0,
                   help="Shift the FRONT icon horizontally in mm (rarely needed).")
    p.add_argument("--front-offset-y", type=float, default=0.0,
                   help="Shift the FRONT icon vertically in mm (rarely needed).")
    p.add_argument("--margin-mm", type=float, default=10.0,
                   help="Batch mode: minimum margin around the grid in mm (default 10).")
    p.add_argument("--grid-gap-mm", type=float, default=0.0,
                   help="Batch mode: gap between grid cells in mm (default 0).")
    p.add_argument("--flip", choices=("long-edge", "short-edge"), default="long-edge",
                   help="Batch mode: how the printer flips the page in duplex. "
                        "'long-edge' (default) mirrors columns; 'short-edge' mirrors rows.")
    args = p.parse_args()

    if args.batch:
        if args.front or args.back:
            print("error: --batch and positional front/back are mutually exclusive",
                  file=sys.stderr)
            sys.exit(2)
        try:
            pairs = list(parse_batch_file(args.batch))
        except (FileNotFoundError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        if not pairs:
            print(f"error: no pairs found in {args.batch}", file=sys.stderr)
            sys.exit(1)
    else:
        if not args.front or not args.back:
            print("error: provide front + back icons, or use --batch FILE",
                  file=sys.stderr)
            sys.exit(2)
        pairs = [(args.front, args.back)]

    # Resolve every icon up-front so we fail fast on a typo.
    resolved = []
    for fr, bk in pairs:
        try:
            resolved.append((find_icon(fr), find_icon(bk)))
        except (FileNotFoundError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

    size_px = mm_to_px(args.size_mm)
    cut_marks = not args.no_cut_marks
    front_off = (mm_to_px(args.front_offset_x), mm_to_px(args.front_offset_y))
    back_off = (mm_to_px(args.back_offset_x), mm_to_px(args.back_offset_y))

    pages = []
    if args.batch:
        gap_px = mm_to_px(args.grid_gap_mm)
        margin_px = mm_to_px(args.margin_mm)
        cols, rows, per_sheet = pick_grid(len(resolved), size_px, gap_px, margin_px)
        n_sheets = (len(resolved) + per_sheet - 1) // per_sheet

        print(f"layout: {cols} x {rows} per sheet ({per_sheet} keychains/sheet, "
              f"{n_sheets} sheet{'s' if n_sheets != 1 else ''})")

        for sheet_idx in range(n_sheets):
            chunk = resolved[sheet_idx * per_sheet:(sheet_idx + 1) * per_sheet]
            front_cells = []
            back_cells = []
            for idx, (front_path, back_path) in enumerate(chunk):
                row, col = divmod(idx, cols)
                # Long-edge duplex flip mirrors columns (page rotates around the
                # vertical axis); short-edge mirrors rows.
                if args.flip == "long-edge":
                    back_row, back_col = row, cols - 1 - col
                else:
                    back_row, back_col = rows - 1 - row, col
                front_cells.append((row, col, front_path))
                back_cells.append((back_row, back_col, back_path))

            pages.append(build_grid_page(front_cells, cols, rows, size_px, gap_px,
                                         cut_marks=cut_marks, offset_px=front_off))
            pages.append(build_grid_page(back_cells, cols, rows, size_px, gap_px,
                                         cut_marks=cut_marks, offset_px=back_off))

        for i, (front_path, back_path) in enumerate(resolved, 1):
            print(f"[{i}/{len(resolved)}] front: {front_path}")
            print(f"        back:  {back_path}")
    else:
        for i, (front_path, back_path) in enumerate(resolved, 1):
            print(f"[{i}/{len(resolved)}] front: {front_path}")
            print(f"        back:  {back_path}")
            pages.append(build_page(front_path, size_px, cut_marks=cut_marks, offset_px=front_off))
            pages.append(build_page(back_path, size_px, cut_marks=cut_marks, offset_px=back_off))

    pages[0].save(
        args.output,
        format="PDF",
        resolution=DPI,
        save_all=True,
        append_images=pages[1:],
    )
    print(f"\nwrote {args.output}")
    print(f"  pages: {len(pages)}  ({len(resolved)} keychain{'s' if len(resolved) != 1 else ''})")
    print(f"  icon:  {args.size_mm:g} mm square")
    if args.batch:
        print(f"  flip:  {args.flip}")
    if args.back_offset_x or args.back_offset_y or args.front_offset_x or args.front_offset_y:
        print(
            f"  offsets: front=({args.front_offset_x:+g},{args.front_offset_y:+g}) mm, "
            f"back=({args.back_offset_x:+g},{args.back_offset_y:+g}) mm"
        )
    print("print with: A4, no scaling (100%), duplex on.\n"
          "if alignment is off after one print, measure the offset between\n"
          "front and back, then re-run with --back-offset-x / --back-offset-y\n"
          "(or switch --flip if every back is mirrored from its front).")


if __name__ == "__main__":
    main()
