#!/usr/bin/env python3
"""Generate a print-ready business card for Stan's Loot.

Reuses the gold-bevel/panel rendering from make_icon_card.py so the card
visually matches the keyrings Stan sells.

Usage:
    python3 make_business_card.py [-o stans_loot_card.png] [-s 2048]
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageCms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_icon_card import (
    draw_beveled_frame,
    draw_gradient_panel,
    draw_caption_strip,
)


def build_panel_mask(size_wh, box, radius):
    """Rounded-rect mask sized for a non-square canvas (the keyring helper assumes square)."""
    mask = Image.new("L", size_wh, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


PRINT_MM = (85, 55)  # standard EU/UK business card

# --- text fonts ---------------------------------------------------------------

FONT_PATHS = {
    "bungee":    "/Users/pfoltyn/pzf_keychain/fonts/Bungee-Regular.ttf",
    "fredoka":   "/Users/pfoltyn/pzf_keychain/fonts/Fredoka.ttf",
    "phosphate": ("/System/Library/Fonts/Supplemental/Phosphate.ttc", 1),
    "impact":    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "bold":      "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "regular":   "/System/Library/Fonts/Supplemental/Arial.ttf",
    "marker":    "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf",
    "chalk":     "/System/Library/Fonts/Supplemental/Chalkduster.ttf",
    "unicode":   "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "emoji":     "/System/Library/Fonts/Apple Color Emoji.ttc",
}

# Apple Color Emoji is a bitmap font — only specific pixel sizes load.
# 96 is the smallest "fits anywhere" size; 160 is sharper but heavier.
EMOJI_NATIVE_SIZE = 96


def render_emoji_text(segments, target_h, draw_canvas_size):
    """Render a [(text, font), (emoji_str,'emoji'), ...] sequence into one transparent layer.

    Returns (layer, total_w, total_h). Emoji segments are rendered with Apple
    Color Emoji at its native bitmap size and scaled down to target_h to match
    surrounding text height.
    """
    from PIL import ImageFont
    pieces = []
    total_w = 0
    for text, kind in segments:
        if kind == "emoji":
            f = ImageFont.truetype(FONT_PATHS["emoji"], EMOJI_NATIVE_SIZE)
            tmp = Image.new("RGBA", (EMOJI_NATIVE_SIZE * (len(text) + 1), EMOJI_NATIVE_SIZE * 2),
                            (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((0, 0), text, font=f, embedded_color=True)
            bbox = tmp.getbbox()
            if bbox is None:
                continue
            tmp = tmp.crop(bbox)
            scale = target_h / tmp.height
            new_size = (max(1, int(tmp.width * scale)), target_h)
            tmp = tmp.resize(new_size, Image.LANCZOS)
            pieces.append(("img", tmp))
            total_w += tmp.width
        else:
            font_obj, fill = kind  # (font, fill_color)
            bb = font_obj.getbbox(text)
            seg = Image.new("RGBA", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 8), (0, 0, 0, 0))
            ImageDraw.Draw(seg).text((-bb[0], -bb[1]), text, font=font_obj, fill=fill)
            pieces.append(("img", seg))
            total_w += seg.width

    layer_h = target_h + 4
    layer = Image.new("RGBA", (total_w + 4, layer_h), (0, 0, 0, 0))
    x = 0
    for _, img in pieces:
        # Vertically center on the baseline of the layer.
        y = (layer_h - img.height) // 2
        layer.alpha_composite(img, dest=(x, y))
        x += img.width
    return layer, total_w, layer_h


def font(kind, size):
    from PIL import ImageFont
    spec = FONT_PATHS.get(kind)
    if spec:
        if isinstance(spec, tuple):
            path, idx = spec
        else:
            path, idx = spec, 0
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=idx)
            except OSError:
                pass
    return ImageFont.load_default()


# --- helpers ------------------------------------------------------------------

def text_with_shadow(canvas, pos, text, fnt, fill, shadow_offset=(4, 4),
                      shadow_alpha=170, shadow_blur=2):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(
        (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]),
        text, font=fnt, fill=(0, 0, 0, shadow_alpha),
    )
    sh = sh.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas.alpha_composite(sh)
    ImageDraw.Draw(canvas).text(pos, text, font=fnt, fill=fill)


def paste_thumbnail_tilted(canvas, img_path, center, target_h, angle=0):
    """Drop in a keyring image scaled to a target height, optionally rotated."""
    img = Image.open(img_path).convert("RGBA")
    scale = target_h / img.height
    new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    img = img.resize(new_size, Image.LANCZOS)
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)

    pos = (center[0] - img.width // 2, center[1] - img.height // 2)

    # Soft drop shadow.
    sh_alpha = img.split()[-1].point(lambda v: int(v * 0.55))
    sh_rgb = Image.new("RGB", img.size, (0, 0, 0))
    sh_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh_layer.alpha_composite(
        Image.merge("RGBA", (*sh_rgb.split(), sh_alpha)),
        dest=(pos[0] + max(3, target_h // 30), pos[1] + max(3, target_h // 30)),
    )
    sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(max(3, target_h // 25)))
    canvas.alpha_composite(sh_layer)

    canvas.alpha_composite(img, dest=pos)


# --- card layout --------------------------------------------------------------

def build_card(output_path, size_long=2048, supersample=2):
    aspect = PRINT_MM[0] / PRINT_MM[1]
    w_out = size_long
    h_out = int(round(size_long / aspect))
    rs = supersample
    w, h = w_out * rs, h_out * rs

    # ----- palette (matches stansloot.com) ---------------------------------
    bg_navy   = (26, 28, 50, 255)         # dark backdrop
    yellow    = (255, 213, 75, 255)       # primary accent
    yellow_lt = (255, 230, 130, 255)      # lighter highlight
    coral     = (245, 90, 100, 255)       # red outline / shadow
    white     = (255, 255, 255, 255)
    dark_text = (35, 25, 5, 255)          # text on yellow

    radius = max(20, w // 32)
    accent_w = max(2, int(w * 0.012))

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Solid navy panel with rounded corners.
    bg_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(bg_layer).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=radius, fill=bg_navy
    )
    canvas.alpha_composite(bg_layer)

    # Inner usable region.
    inset = int(w * 0.04)
    ix0, iy0 = inset, inset
    ix1, iy1 = w - inset, h - inset
    inner_w = ix1 - ix0
    inner_h = iy1 - iy0

    # ----- thumbnails: 3 keyrings, top-right --------------------------------
    thumbs = [
        ("done/Rivals/Knife.png", -8),
        ("done/BloxFruits/Dragon_Fruit.png", 0),
        ("done/Adopt Me!/Phoenix_.png", 8),
    ]
    thumb_h = int(inner_h * 0.40)
    gap_x = int(thumb_h * 0.04)
    row_w = len(thumbs) * thumb_h + (len(thumbs) - 1) * gap_x
    row_top = iy0
    row_left = ix1 - row_w
    for i, (p, ang) in enumerate(thumbs):
        if not os.path.exists(p):
            continue
        cx = row_left + i * (thumb_h + gap_x) + thumb_h // 2
        cy = row_top + thumb_h // 2 + (abs(i - (len(thumbs) - 1) / 2) * int(thumb_h * 0.04))
        paste_thumbnail_tilted(canvas, p, (cx, int(cy)), thumb_h, angle=ang)

    # ----- two-tone outlined title: STAN'S / LOOT (Bungee, LOOT tilted) ----
    avail_w_title = row_left - ix0 - int(inset * 0.3)
    avail_h_title = thumb_h
    title_p1 = "STAN'S"
    title_p2 = "LOOT"
    title_size = int(h * 0.42)
    while True:
        f = font("bungee", title_size)
        bb1 = f.getbbox(title_p1)
        bb2 = f.getbbox(title_p2)
        max_w = max(bb1[2] - bb1[0], bb2[2] - bb2[0])
        line_h = max(bb1[3] - bb1[1], bb2[3] - bb2[1])
        total_h = line_h * 2 + int(line_h * 0.05)
        if (max_w <= avail_w_title and total_h <= avail_h_title) or title_size < 30:
            break
        title_size -= 4
    title_font = f
    bb1 = title_font.getbbox(title_p1)
    bb2 = title_font.getbbox(title_p2)
    line_h = max(bb1[3] - bb1[1], bb2[3] - bb2[1])
    line_gap = int(line_h * 0.05)
    title_block_h = line_h * 2 + line_gap
    title_top = row_top + (thumb_h - title_block_h) // 2
    title_x = ix0
    stroke_w = max(2, int(title_size * 0.06))

    # Line 1 — STAN'S in white with coral outline (no tilt).
    d = ImageDraw.Draw(canvas)
    d.text((title_x - bb1[0], title_top - bb1[1]), title_p1, font=title_font,
           fill=white, stroke_width=stroke_w, stroke_fill=coral)

    # Line 2 — LOOT in yellow with coral outline, tilted -3° to match the
    # site's wobble animation (rendered to its own layer, rotated, composited).
    p2_w = bb2[2] - bb2[0]
    p2_h = bb2[3] - bb2[1]
    p2_layer = Image.new(
        "RGBA",
        (p2_w + stroke_w * 4, p2_h + stroke_w * 4),
        (0, 0, 0, 0),
    )
    ImageDraw.Draw(p2_layer).text(
        (-bb2[0] + stroke_w * 2, -bb2[1] + stroke_w * 2),
        title_p2, font=title_font,
        fill=yellow, stroke_width=stroke_w, stroke_fill=coral,
    )
    p2_layer = p2_layer.rotate(3, resample=Image.BICUBIC, expand=True)
    line2_y = title_top + line_h + line_gap
    paste_x = title_x - stroke_w * 2
    paste_y = line2_y - stroke_w * 2 - (p2_layer.height - (p2_h + stroke_w * 4)) // 2
    canvas.alpha_composite(p2_layer, dest=(paste_x, paste_y))

    # ----- yellow marquee strip (tilted -1.2° like the site) ---------------
    # Website text: 🔥 LIMITED STOCK · ⭐ HANDMADE · 🔧 PICK FRONT + BACK · 🚚 SCHOOL PICKUP ONLY · 💸 NO TAXES (I'M 10)
    # Rendered as alternating text/emoji segments so Apple Color Emoji shows.
    marquee_h = int(inner_h * 0.20)
    mq_y0 = row_top + thumb_h + int(inner_h * 0.04)
    mq_y1 = mq_y0 + marquee_h
    mq_radius = marquee_h // 4

    # Build the marquee strip on a wider transparent layer so we can rotate it.
    strip_w = ix1 - ix0
    strip_h = marquee_h
    strip_layer = Image.new("RGBA", (strip_w, strip_h), (0, 0, 0, 0))
    ImageDraw.Draw(strip_layer).rounded_rectangle(
        [0, 0, strip_w - 1, strip_h - 1], radius=mq_radius, fill=yellow,
        outline=coral, width=max(2, int(strip_h * 0.06)),
    )

    # Mixed text + emoji marquee.
    items = [
        ("🔥", "emoji"), (" LIMITED STOCK   ", "text"),
        ("⭐", "emoji"), (" HANDMADE   ", "text"),
        ("🔧", "emoji"), (" PICK FRONT + BACK   ", "text"),
        ("🚚", "emoji"), (" SCHOOL PICKUP ONLY   ", "text"),
        ("💸", "emoji"), (" NO TAXES (I'M 10)", "text"),
    ]
    text_size = int(strip_h * 0.45)
    while True:
        text_font = font("bungee", text_size)
        segs = []
        for content, kind in items:
            if kind == "emoji":
                segs.append((content, "emoji"))
            else:
                segs.append((content, (text_font, dark_text)))
        layer, total_w, layer_h = render_emoji_text(segs, target_h=int(strip_h * 0.55),
                                                    draw_canvas_size=strip_layer.size)
        if total_w <= strip_w - int(strip_h * 0.6) or text_size < 12:
            break
        text_size -= 2

    layer_x = (strip_w - layer.width) // 2
    layer_y = (strip_h - layer.height) // 2
    strip_layer.alpha_composite(layer, dest=(layer_x, layer_y))

    # Tilt the entire strip -1.2° (matches site rotation).
    strip_layer = strip_layer.rotate(1.2, resample=Image.BICUBIC, expand=True)
    paste_pos = (
        ix0 + (strip_w - strip_layer.width) // 2,
        mq_y0 + (strip_h - strip_layer.height) // 2,
    )
    canvas.alpha_composite(strip_layer, dest=paste_pos)

    # ----- yellow CTA strip with URL ---------------------------------------
    cta_h = int(inner_h * 0.22)
    cta_y0 = iy1 - cta_h
    cta_y1 = iy1
    cta_radius = cta_h // 3

    cta_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cta_layer)
    # Two-stop gradient: yellow on left, coral on right (matches the website button).
    grad = Image.new("RGB", (ix1 - ix0, 1))
    gp = grad.load()
    for x in range(grad.width):
        t = x / max(1, grad.width - 1)
        gp[x, 0] = (
            int(yellow[0] * (1 - t) + coral[0] * t),
            int(yellow[1] * (1 - t) + coral[1] * t),
            int(yellow[2] * (1 - t) + coral[2] * t),
        )
    grad = grad.resize((ix1 - ix0, cta_y1 - cta_y0)).convert("RGBA")
    # Mask to a rounded-rect.
    mask = Image.new("L", (ix1 - ix0, cta_y1 - cta_y0), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, mask.width - 1, mask.height - 1], radius=cta_radius, fill=255
    )
    grad.putalpha(mask)
    canvas.alpha_composite(grad, dest=(ix0, cta_y0))

    site = "STANSLOOT.COM"
    site_size = int(cta_h * 0.55)
    while True:
        site_font = font("bungee", site_size)
        sb = site_font.getbbox(site)
        if (sb[2] - sb[0]) <= (ix1 - ix0) - int(cta_h * 0.6) or site_size < 30:
            break
        site_size -= 4
    site_font = font("bungee", site_size)
    sb = site_font.getbbox(site)
    site_w = sb[2] - sb[0]
    site_h_px = sb[3] - sb[1]
    site_pos = (
        (ix0 + ix1) // 2 - site_w // 2 - sb[0],
        (cta_y0 + cta_y1) // 2 - site_h_px // 2 - sb[1],
    )
    site_stroke = max(2, int(site_size * 0.05))
    ImageDraw.Draw(canvas).text(
        site_pos, site, font=site_font,
        fill=white, stroke_width=site_stroke, stroke_fill=(50, 25, 5, 255),
    )

    # ----- thin outer accent border ----------------------------------------
    border_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(border_layer).rounded_rectangle(
        [accent_w // 2, accent_w // 2, w - accent_w // 2 - 1, h - accent_w // 2 - 1],
        radius=radius, outline=yellow, width=accent_w,
    )
    canvas.alpha_composite(border_layer)

    # ----- finish: downsample, embed sRGB + DPI ----------------------------
    if rs != 1:
        canvas = canvas.resize((w_out, h_out), Image.LANCZOS)
    canvas = canvas.convert("RGB")

    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    dpi = round(w_out * 25.4 / PRINT_MM[0])
    canvas.save(output_path, dpi=(dpi, dpi), icc_profile=srgb_profile)
    return output_path, dpi


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output", default="stans_loot_card.png")
    p.add_argument("-s", "--size", type=int, default=2048,
                   help="long-edge size in pixels (default 2048 ≈ 612 DPI for 85mm)")
    args = p.parse_args()
    out, dpi = build_card(args.output, size_long=args.size)
    print(f"wrote {out}  ({dpi} DPI for {PRINT_MM[0]}×{PRINT_MM[1]} mm)")


if __name__ == "__main__":
    main()
